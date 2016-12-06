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
    s = Search()
    form = forms.SearchForm(request.GET)
    results = search.Results(page=1)

    if form.is_valid():
        and_queries = []
        or_queries = []

        # Search fields
        if 'title' in form.cleaned_data.get('search_fields'):
            or_queries.append(Q("match", title=form.cleaned_data['search']))
        if 'tags' in form.cleaned_data.get('search_fields'):
            or_queries.append(Q("match", tags=form.cleaned_data['search']))
        if 'creator' in form.cleaned_data.get('search_fields'):
            or_queries.append(Q("match", creator=form.cleaned_data['search']))

        # Work types must match
        if 'photos' in form.cleaned_data.get('work_types'):
            and_queries.append(
                            Q('bool',
                            should=[Q("term", provider=provider) for provider in settings.WORK_TYPES['photos']]
                            ))
        if 'cultural' in form.cleaned_data.get('work_types'):
            and_queries.append(
                            Q('bool',
                            should=[Q("term", provider=provider) for provider in settings.WORK_TYPES['cultural']]
                            ))


        if len(or_queries) > 0 or len(and_queries) > 0:

            q = Q('bool',
                  should=or_queries,
                  must=Q('bool', should=and_queries),
                  minimum_should_match=1)
            s = s.query(q)
            response = s.execute()
            results.pages = int(int(response.hits.total) / forms.PER_PAGE)
            results.page = form.cleaned_data['page'] or 1
            start = results.page
            end = start + forms.PER_PAGE - 1
            for r in s[start - 1:end]:
                results.items.append(r)
    else:
        form = forms.SearchForm(initial=forms.SearchForm.initial_data)

    return render(request, 'results.html',
                  {'form': form,
                   'results': results,})


def provider_apis(request, provider=None):
    """Search by passing queries through to provider apis"""
    results = {}
    form = forms.SearchForm(request.GET)
    if form.is_valid():
        for k in forms.SearchForm.initial_data:
            if k not in form.cleaned_data or not form.cleaned_data[k]:
                form.cleaned_data[k] = forms.SearchForm.initial_data[k]
        for p in form.cleaned_data['providers']:
            if p:
                results[p] = search_funcs[p](search=form.cleaned_data['search'],
                                             licenses=form.cleaned_data['licenses'],
                                             page=form.cleaned_data['page'],
                                             per_page=forms.PROVIDER_PER_PAGE)
    else:
        initial_data = forms.SearchForm.initial_data
        form = forms.SearchForm(initial=initial_data)

    return render(request, 'provider-results.html',
                           {'form': form,
                            'results': results,
                            'license_map': licenses.license_map_from_partners()})


def by_provider(request, provider):
    return provider_apis(request, provider=provider)

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
