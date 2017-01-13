import logging

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.connections import connections

from imageledger import forms, search, licenses, models
from imageledger.handlers.handler_500px import photos as search_500
from imageledger.handlers.handler_rijks import photos as search_rijks
from imageledger.handlers.handler_flickr import photos as search_flickr
from imageledger.handlers.handler_wikimedia import photos as search_wikimedia

log = logging.getLogger(__name__)

# Search by source


search_funcs = {
    "fpx": search_500,
    "flickr": search_flickr,
    "rijks": search_rijks,
    "wikimedia": search_wikimedia,
}

@ensure_csrf_cookie
def index(request):
    s = Search(index=settings.ELASTICSEARCH_INDEX)
    s = s.sort({'_score': {'order': 'desc'}})
    form = forms.SearchForm(request.GET)
    results = search.Results(page=1)

    if form.is_valid():
        if form.cleaned_data.get('search'):
            and_queries = []
            or_queries = []

            # Search fields
            if 'title' in form.cleaned_data.get('search_fields'):
                or_queries.append(Q("match", title=form.cleaned_data['search']))
            if 'tags' in form.cleaned_data.get('search_fields'):
                or_queries.append(Q("match", tags=form.cleaned_data['search']))
            if 'creator' in form.cleaned_data.get('search_fields'):
                or_queries.append(Q("match", creator=form.cleaned_data['search']))

            # Limit to explicit providers first, and then to work providers second, if provided.
            # If provider is supplied, work providers is ignored. TODO revisit this logic as it
            # could be confusing to end users
            work_providers = set()
            if form.cleaned_data.get('work_types'):
                for t in form.cleaned_data.get('work_types'):
                    for p in settings.WORK_TYPES[t]:
                        work_providers.add(p)

            limit_to_providers = form.cleaned_data.get('providers') or work_providers

            for provider in limit_to_providers:
                and_queries.append(
                                Q('bool',
                                should=[Q("term", provider=provider)]
                                ))

            if len(or_queries) > 0 or len(and_queries) > 0:
                q = Q('bool',
                      should=or_queries,
                      must=Q('bool', should=and_queries),
                      minimum_should_match=1)
                s = s.query(q)
                response = s.execute()
                results.pages = int(int(response.hits.total) / settings.RESULTS_PER_PAGE)
                results.page = form.cleaned_data['page'] or 1
                start = (results.page - 1) * settings.RESULTS_PER_PAGE
                end = start + settings.RESULTS_PER_PAGE
                for r in s[start:end]:
                    results.items.append(r)
    else:
        form = forms.SearchForm(initial=forms.SearchForm.initial_data)

    return render(request, 'results.html',
                  {'form': form,
                   'results': results,})

def by_image(request):
    """Load an image in detail view, passing parameters by query string so that
    we can either load an image from an external provider or from our own datastore."""
    license_version = licenses.license_map_from_partners()[request.GET.get('provider')]['version']
    license_url = licenses.get_license_url(request.GET.get('license'), license_version)
    remaining = dict((k, request.GET[k]) for k in request.GET)  # The vals in request.GET are lists, so flatten
    remaining.update({'license_version': license_version})
    return render(request, 'detail.html',
                  {'image': remaining,
                   'license_url': license_url,
                   })


def detail(request, identifier):
    obj = get_object_or_404(models.Image, identifier=identifier)
    if request.user.is_authenticated():
        # Is it a favorite?
        obj.is_favorite = models.Favorite.objects.filter(user=request.user, image=obj).exists()
    license_url = licenses.get_license_url(obj.license, obj.license_version)
    return render(request, 'detail.html',
                  {'image': obj,
                   'license_url': license_url,})
