import itertools
import logging
import json
import time
import urllib
import requests

from django.conf import settings
from imageledger import models, signals, search
from django.db.utils import IntegrityError
from django.utils import timezone

from imageledger import licenses
from imageledger.handlers.utils import *

BASE_URL = 'http://www.europeana.eu'
ENDPOINT_PHOTOS = BASE_URL + '/api/v2/search.json'

SOURCE_NAME = "europeana"

DELAY_SECONDS = 1  # Time to wait between API requests

log = logging.getLogger(__name__)

def photos(search=None, page='*', per_page=20, **kwargs):
    params = {
        'query': 'NOT PROVIDER:"Rijksmuseum"',
        'media': True,
        'qf': ['IMAGE_SIZE:large', 'IMAGE_SIZE:extra_large', 'TYPE:IMAGE',],
        'reusability': 'open',
        'profile': 'rich',
        'thumbnail': True,
        'rows': per_page,
        'cursor': page,
        'wskey': settings.EUROPEANA_API_KEY,
    }
    r = requests.get(ENDPOINT_PHOTOS, params=params)
    results = r.json()
    results['pages'] = int(int(results['totalResults']) / per_page)
    return results

def serialize(result):
    """For a given Europeana result, map that to our database"""
    if 'edmIsShownBy' in result:
        url = result['edmIsShownBy'][0]

        image = models.Image(url=url)
        thumbnail = 'https://www.europeana.eu/api/v2/thumbnail-by-url.json?size=w200&type=IMAGE&'
        image.thumbnail = thumbnail + urllib.parse.urlencode({'uri': url})
        image.source = SOURCE_NAME
        image.provider = SOURCE_NAME
        image.creator = result['dcCreator'][0] if 'dcCreator' in result else None
        license, version = licenses.url_to_license(result['rights'][0])
        image.license = license
        image.license_version = version
        image.foreign_landing_url = result['guid']
        image.foreign_identifier = result['id']
        image.title = result['title'][0]
        image.identifier = signals.create_identifier(image.url)
        image.last_synced_with_source = timezone.now()

        tag_names = []
        # Tags, if available
        if 'edmConceptPrefLabelLangAware' in result and 'en' in result['edmConceptPrefLabelLangAware']:
            # Each one of these is a tag
            for tag_label in result['edmConceptPrefLabelLangAware']['en']:
                #log.debug("Adding tag %s", tag_label)
                models.Tag.objects.get_or_create(name=tag_label.lower(), source=SOURCE_NAME)
                tag_names.append(tag_label)
        image.tags_list = tag_names
        #log.debug("'%s' from %s", image.title, image.provider)
        return image

def walk(page="*", per_page=200):
    """Walk through a set of search results and collect items to serialize"""
    has_more = True

    while has_more:
        results = photos(page=page, per_page=per_page)
        page = results.get('nextCursor')
        if not page:
            has_more = False
        for result in results['items']:
            yield result
        time.sleep(2)
