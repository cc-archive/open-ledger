import itertools
import logging
import time
from pprint import pprint

import requests

from django.conf import settings
from imageledger import models, signals, search
from django.db.utils import IntegrityError
from django.utils import timezone

from imageledger.handlers.utils import *

BASE_URL = 'http://www.metmuseum.org'
ENDPOINT_PHOTOS = BASE_URL + '/api/collection/openaccessobjectids'
ENDPOINT_DETAIL = BASE_URL + '/api/collection/collectionobject/'
ENDPOINT_BASE_IMAGE_URL = 'http://images.metmuseum.org/crdimages/'

LICENSE_VERSION = "1.0"
LICENSE_URL = "https://creativecommons.org/publicdomain/zero/1.0/"

PROVIDER_NAME = "met"
SOURCE_NAME = "met"

DELAY_SECONDS = 2  # Time to wait between API requests

THUMBNAIL_WIDTH = 200

log = logging.getLogger(__name__)


def photos(search=None, page=1, per_page=20, **kwargs):
    # This will retrieve the complete collection of openly-licensed images
    # Rijks pages are zero-indexed, so always subtract one before the request
    params = {}
    r = requests.get(ENDPOINT_PHOTOS, params=params)
    results = r.json()
    return results

def serialize(result):
    """For a given Met result, map that to our database"""
    imageinfos = result['ImageInfo']
    thumbnail = None
    url = None
    for info in imageinfos:
        if info['PrimaryDisplay']:
            # Use this one
            thumbnail = ENDPOINT_BASE_IMAGE_URL + info['Thumbnail']
            url = ENDPOINT_BASE_IMAGE_URL + info['LargeWebsite']
            break
    if not url:
        log.warning("Did not get an image URL for %s", result)
        return
    image = models.Image(url=url)
    image.provider = PROVIDER_NAME
    image.source = SOURCE_NAME

    # Creator might be a few fields
    tombstone = result['Tombstone']
    for t in tombstone:
        if t['Name'] == 'Maker:':  # Note trailing colon :(
            image.creator = t['Value']
        # TBD other metadata
    image.thumbnail = thumbnail
    image.license = "cc0"
    image.license_version = '1.0'
    image.foreign_landing_url = ""
    image.foreign_identifier = result['CollectionObject']['CRDID']
    image.title = result['CollectionObject']['Title']
    image.identifier = signals.create_identifier(image.url)
    image.last_synced_with_source = timezone.now()
    log.info("Adding image %s identifier %s", image.title, image.identifier)
    return image

def walk(page=1, per_page=200):
    """Walk through a set of search results and collect items to serialize"""
    results = photos()
    for identifier in results:
        # Retrieve the result
        url = ENDPOINT_DETAIL + str(identifier)
        r = requests.get(url, headers={'accept': 'text/html'})
        result = r.json()
        yield result
        time.sleep(DELAY_SECONDS)
