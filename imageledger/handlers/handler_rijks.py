import itertools
import logging
import time

import requests

from elasticsearch import helpers
from django.conf import settings
from imageledger import models, signals, search
from django.db.utils import IntegrityError
from django.utils import timezone

from imageledger.handlers.utils import *

BASE_URL = 'https://www.rijksmuseum.nl'
ENDPOINT_PHOTOS = BASE_URL + '/api/en/collection'

LICENSE_VERSION = "1.0"
LICENSE_URL = "https://creativecommons.org/publicdomain/zero/1.0/"

PROVIDER_NAME = "rijksmuseum"
SOURCE_NAME = "rijksmuseum"

DELAY_SECONDS = 2  # Time to wait between API requests

THUMBNAIL_WIDTH = 200

log = logging.getLogger(__name__)


def photos(search=None, page=1, per_page=20, **kwargs):
    # Rijks pages are zero-indexed, so always subtract one before the request
    p = int(page) - 1
    params = {
        'format': 'JSON',
        'q': search,
        'key': settings.API_RIJKS,
        'imgonly': 'True',  # This doesn't seem to have an effect, so filter
        'culture': 'en',
        'p': p, # Page number
        'ps': per_page,  # Results per page
    }
    r = requests.get(ENDPOINT_PHOTOS, params=params)
    results = r.json()

    # Since the imgonly parameter doesn't work, filter ourselves and cut down the result set
    filtered = [res for res in results.get('artObjects') if res.get('webImage')]
    results['artObjects'] = filtered[:per_page]

    # Rijks doesn't give us a nice set of pages, so do that ourselves
    results['page'] = int(page)
    results['pages'] = int(int(results['count']) / per_page)
    return results


def serialize(result):
    """For a given Rijks result, map that to our database"""
    url = result['webImage']['url']

    # Thumbnails from Rijks are dynamic; let's make them 200 wide
    if url.endswith('=s0'):
        thumbnail = url[:-3] + '=s' + str(THUMBNAIL_WIDTH)
    image = models.Image(url=url)
    image.provider = PROVIDER_NAME
    image.source = SOURCE_NAME
    image.creator = result['principalOrFirstMaker']
    image.thumbnail = thumbnail
    image.license = "CC0"
    image.license_version = '1.0'
    image.foreign_landing_url = result['links']['web']
    image.foreign_identifier = result['webImage']['guid']
    image.width = result['webImage']['width']
    image.height = result['webImage']['height']
    image.title = result['longTitle']
    image.identifier = signals.create_identifier(image.url)
    image.last_synced_with_source = timezone.now()
    return image

def walk(page=1, per_page=200):
    """Walk through a set of search results and collect items to serialize"""

    has_more = True
    while has_more:
        results = photos(page=page, per_page=per_page)
        for result in results['artObjects']:
            if 'copyrightHolder' in result:
                log.warn("Skipping image with copyright holder value: %s, %s", result['webImage']['url'], result['copyrightHolder'])
                continue
            if not result['permitDownload']:
                log.warn("Skipping image where permitDownload is false: %s", result['webImage']['url'])
                continue
            yield result
        page += 1
        time.sleep(2)
