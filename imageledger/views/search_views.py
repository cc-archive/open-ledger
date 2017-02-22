import logging
from functools import reduce

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.connections import connections

from imageledger import forms, search, licenses, models

log = logging.getLogger(__name__)

@ensure_csrf_cookie
def index(request):
    s = Search(index=settings.ELASTICSEARCH_INDEX)
    s = s.sort({'_score': {'order': 'desc'}})
    form = forms.SearchForm(request.GET)
    results = search.Results(page=1)

    if form.is_valid():
        if form.cleaned_data.get('search'):
            per_page = int(form.cleaned_data.get('per_page') or forms.RESULTS_PER_PAGE_DEFAULT)
            and_queries = []
            or_queries = []

            # Search fields
            if 'title' in form.cleaned_data.get('search_fields'):
                or_queries.append(Q("query_string",
                                    default_operator="AND",
                                    fields=["title"],
                                    query=form.cleaned_data['search']))
            if 'tags' in form.cleaned_data.get('search_fields'):
                or_queries.append(Q("query_string",
                                    default_operator="AND",
                                    fields=["tags"],
                                    query=form.cleaned_data['search']))
            if 'creator' in form.cleaned_data.get('search_fields'):
                or_queries.append(Q("query_string",
                                    default_operator="AND",
                                    fields=["creator"],
                                    query=form.cleaned_data['search']))

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

            # License limitations
            license_filters = []
            if form.cleaned_data.get('licenses'):
                # If there's a license restriction, unpack the licenses and search for them
                l_groups = form.cleaned_data.get('licenses')
                license_values = []
                for l_group in l_groups:
                    license_values.append([l.lower() for l in licenses.LICENSE_GROUPS[l_group]])
                license_filters = list(reduce(set.intersection, map(set, license_values)))

            if len(or_queries) > 0 or len(and_queries) > 0:
                q = Q('bool',
                      should=or_queries,
                      must=Q('bool',
                             should=and_queries),
                      minimum_should_match=1)
                s = s.query(q)
                if license_filters:
                    s = s.filter('terms', license=license_filters)
                response = s.execute()
                results.pages = int(int(response.hits.total) / per_page)
                results.page = form.cleaned_data['page'] or 1
                start = (results.page - 1) * per_page
                end = start + per_page
                for r in s[start:end]:
                    results.items.append(r)
    else:
        form = forms.SearchForm(initial=forms.SearchForm.initial_data)

    return render(request, 'results.html',
                  {'form': form,
                   'work_types': settings.WORK_TYPES,
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
