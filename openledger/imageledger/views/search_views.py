from django.shortcuts import render
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.connections import connections

from imageledger import forms, search, licenses
from imageledger.handlers.handler_500px import photos as search_500
from imageledger.handlers.handler_rijks import photos as search_rijks
from imageledger.handlers.handler_flickr import photos as search_flickr
from imageledger.handlers.handler_wikimedia import photos as search_wikimedia

PER_PAGE = 20

# Search by source
WORK_TYPES = {
    'photos': ['flickr'],
    'cultural': ['rijksmuseum']
}

search_funcs = {
    "fpx": search_500,
    "flickr": search_flickr,
    "rijks": search_rijks,
    "wikimedia": search_wikimedia,
}

def index(request):
    s = Search()
    form = forms.SearchForm(request.GET)
    search_data_for_pagination = {}
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
            and_queries.append(Q("term", provider=WORK_TYPES['photos'][0]))  # FIXME make this an OR
        if 'cultural' in form.cleaned_data.get('work_types'):
            and_queries.append(Q("term", provider=WORK_TYPES['cultural'][0]))

        if len(or_queries) > 0 or len(and_queries) > 0:

            q = Q('bool',
                  should=or_queries,
                  must=Q('bool', should=and_queries),
                  minimum_should_match=1)
            s = s.query(q)
            response = s.execute()
            results.pages = int(int(response.hits.total) / PER_PAGE)

            start = results.page
            end = start + PER_PAGE
            for r in s[start - 1:end]:
                results.items.append(r)
            search_data_for_pagination = {i: form.cleaned_data.get(i) for i in form.cleaned_data if i != 'page'}

    else:
        form = forms.SearchForm(initial=forms.SearchForm._initial_data)


    return render(request, 'results.html',
                  {'form': form,
                   'results': results,
                   'search_data_for_pagination': search_data_for_pagination})


def provider_apis(request, provider=None):
    """Search by passing queries through to provider apis"""
    results = {}
    form = forms.SearchForm(request.GET)
    search_data_for_pagination = {}

    if form.is_valid():
        for p in form.cleaned_data['providers']:
            results[p] = search_funcs[p](search=form.cleaned_data['search'],
                                         licenses=form.cleaned_data['licenses'],
                                         page=form.cleaned_data['page'],
                                         per_page=PER_PAGE)
        search_data_for_pagination = {i: form.cleaned_data.get(i) for i in form.cleaned_data}
    else:
        initial_data = forms.SearchForm._initial_data
        initial_data.update({'providers': forms.PROVIDERS_ALL})
        form = forms.SearchForm(initial=initial_data)

    return render(request, 'provider-results.html',
                           {'form': form,
                            'results': results,
                            'search_data_for_pagination': search_data_for_pagination,
                            'license_map': licenses.license_map_from_partners()})


def by_provider(request, provider):
    return provider_apis(request, provider=provider)

def by_image(request):
    pass

def detail(request):
    pass
