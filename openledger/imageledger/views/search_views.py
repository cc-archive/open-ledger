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
    form = forms.SearchForm()
    search_data = []
    results = search.Results(page=1)
    search_data_for_pagination = {i: search_data[i] for i in search_data if i != 'page'}

    return render(request, 'results.html',
                  {'form': form,
                   'results': results,
                   'search_data': search_data,
                   'search_data_for_pagination': search_data_for_pagination})
