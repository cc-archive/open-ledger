import logging
from urllib.parse import parse_qs
from pprint import pprint

import requests
from requests_oauthlib import OAuth1Session, OAuth1
from oauthlib.oauth2 import BackendApplicationClient
from django.conf import settings
from django.db.utils import IntegrityError
from django.utils import timezone

from imageledger.licenses import license_match
from imageledger.handlers.utils import *

BASE_URL = 'https://api.500px.com'
ENDPOINT_PHOTOS = BASE_URL + '/v1/photos/search'

PROVIDER_NAME = '500px'
SOURCE_NAME = '500px'

IMAGE_SIZE_THUMBNAIL = 3  # 200x200
IMAGE_SIZE_FULL = 1080 # 1080x

log = logging.getLogger(__name__)

# 500px will return these values as integers, so keep them as integers
LICENSES = {
    "BY": 4,
    "BY-NC": 1,
    "BY-ND": 5,
    "BY-SA": 6,
    "BY-NC-ND": 2,
    "BY-NC-SA": 3,
    "PDM": 7,
    "CC0": 8,
}
LICENSE_VERSION = "3.0"

LICENSE_LOOKUP = {v: k for k, v in LICENSES.items()}

def auth():
    return OAuth1(settings.API_500PX_KEY, client_secret=settings.API_500PX_SECRET)

def photos(search=None, licenses=["ALL"], page=1, per_page=20, extra={}, **kwargs):
    params = {
        'license_type': license_match(licenses, LICENSES),
        'term': search,
        'page': page,
        'rpp': per_page,
        'nsfw': False,
        'image_size': "%s,%s" % (IMAGE_SIZE_THUMBNAIL, IMAGE_SIZE_FULL)
    }
    params.update(extra)
    r = requests.get(ENDPOINT_PHOTOS, params=params, auth=auth())
    assert r.status_code == 200
    return r.json()

def serialize(result):
    """For a given 500px result, map that to our database"""
    url = result['images'][1]['https_url']
    image = models.Image(url=url)
    image.thumbnail = result['images'][0]['https_url']
    image.provider = PROVIDER_NAME
    image.source = SOURCE_NAME
    image.creator = result['user']['username']
    try:
        image.license = LICENSE_LOOKUP[result['license_type']].lower()
    except KeyError:
        # We got an unknown license, so just skip this
        return None
    image.license_version = LICENSE_VERSION
    image.foreign_landing_url = "https://500px.com/" + result['url']
    image.foreign_identifier = result['id']
    image.title = result['name']
    image.identifier = signals.create_identifier(image.url)
    image.last_synced_with_source = timezone.now()
    return image

def walk(page=1, per_page=100):
    """Walk through a set of search results and collect items to serialize"""

    has_more = True
    while has_more:
        results = photos(page=page, per_page=per_page, extra={'sort': 'created_at'})
        for result in results.get('photos'):
            yield result
        page += 1
        time.sleep(2)
