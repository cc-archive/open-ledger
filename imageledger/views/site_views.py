import logging
import re

from django.conf import settings
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from elasticsearch_dsl import Search, Q

from imageledger import forms, search, licenses, models

log = logging.getLogger(__name__)

CACHE_STATS_DURATION = 60 * 60  # 1 hour

@cache_page(CACHE_STATS_DURATION)
def about(request):
    """Information about the current site, its goals, and what content is loaded"""
    # Provider counts
    providers = []
    for provider in sorted(settings.PROVIDERS.keys()):
        s = Search()
        q = Q('term', provider=provider)
        s = s.query(q)
        response = s.execute()
        if response.hits.total > 0:
            data = settings.PROVIDERS[provider]
            total = intcomma(response.hits.total)
            data.update({'hits': total})
            providers.append(data)
    return render(request, "about.html", {'providers': providers})

def intcomma(value):
    # Adapted from https://github.com/django/django/blob/master/django/contrib/humanize/templatetags/humanize.py
    orig = str(value)
    new = re.sub(r"^(-?\d+)(\d{3})", r'\g<1>,\g<2>', orig)
    if orig == new:
        return new
    else:
        return intcomma(new)
