from django.shortcuts import render
from elasticsearch_dsl import Search, Q

from imageledger import forms, search

PER_PAGE = 20

# Search by source
WORK_TYPES = {
    'photos': ['flickr'],
    'cultural': ['rijksmuseum']
}

def index(request):
    search.init()
    form = forms.SearchForm(request.GET)
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

        q = Q('bool',
              should=or_queries,
              must=Q('bool', should=and_queries),
              minimum_should_match=1)
        s = s.query(q)
        response = s.execute()
        results.pages = int(int(response.hits.total) / PER_PAGE)
        start = results.page
        end = start + PER_PAGE
        for r in s[start -1:end]:
            results.items.append(r)

    results = search.Results(page=1)
    search_data_for_pagination = {i: form.cleaned_data[i] for i in form.cleaned_data if i != 'page'}

    return render(request, 'results.html',
                  {'form': form,
                   'results': results,
                   'search_data': {},
                   'search_data_for_pagination': search_data_for_pagination})
