import itertools
import logging
import time
from pprint import pprint
import json

from elasticsearch import helpers

import requests
from urllib.parse import parse_qs
from requests_oauthlib import OAuth1Session, OAuth1
from oauthlib.oauth2 import BackendApplicationClient

from django.conf import settings
from imageledger import models, signals, search
from django.db.utils import IntegrityError
from django.utils import timezone

MAX_REQUESTS_PER_DAY = 10000  # Per their API agreement

LICENSE_VERSION = "1.0"
LICENSE_URL = "https://creativecommons.org/publicdomain/zero/1.0/"

BASE_URL = 'http://api.repo.nypl.org/api/v1'
ENDPOINT_PHOTOS = BASE_URL + '/items/search'
ENDPOINT_DETAIL = BASE_URL + '/items/'

PROVIDER_NAME = "nypl"
SOURCE_NAME = "nypl"

log = logging.getLogger(__name__)

def auth():
    return 'Token token=' + settings.NYPL_KEY

def photos(search=None, page=1, per_page=500, **kwargs):
    params = {
        'q': 'still image',
        'publicDomainOnly': 'true',
        'field': 'typeOfResource',
        'page': page,
        'per_page': per_page,
    }
    r = requests.get(ENDPOINT_PHOTOS, params=params, headers={'Authorization': auth()})
    results = r.json()['nyplAPI']['response']['result']
    return results

def import_from_file(from_file):
    """Import from an NDJSON file"""
    # ndjson files are newline delimited
    results = []
    tags = {}
    for line in open(from_file):
        result = json.loads(line)
        if 'still image' in result['resourceType'] and result.get('captures') and len(result.get('captures')):
            url = result.get('captures')[0]
            url = url[:-3] + 't=w'  # 760 jpg, but it's the largest we're guaranteed to find
            thumbnail = url[:-3] + 't=r' # 300px thumbnail
            image = models.Image(url=url)
            image.provider = PROVIDER_NAME
            image.source = SOURCE_NAME
            if result.get('contributor'):
                if 'contributorName' in result.get('contributor')[0]:
                    image.creator = result['contributor'][0]['contributorName']
            image.thumbnail = thumbnail
            image.license = "CC0"
            image.license_version = '1.0'
            image.foreign_landing_url = result['digitalCollectionsURL']
            image.foreign_identifier = result['UUID']
            image.title = result['title']
            image.identifier = signals.create_identifier(image.url)
            image.last_synced_with_source = timezone.now()

            tag_names = [topic['text'] for topic in result.get('subjectName')]
            for tag in tag_names:
                tags[tag] = models.Tag(name=tag, source='nypl')
            image.tags_list = tag_names
            results.append(image)
    # Create the tags objects
    log.debug("Bulk creating %d new tags", len(tags.values()))
    models.Tag.objects.bulk_create(tags.values())
    return results

def serialize(result):
    """For each NYPL result, map that to our database"""
    pass # TODO implement from API

def walk(page=1, per_page=200, from_file=None):
    """Walk through a set of search results and collect items to serialize"""
    has_more = True
    while has_more:
        if from_file:
            results = import_from_file(from_file)
        else:
            results = photos(page=page, per_page=per_page)
        for result in results:
            yield result
        page += 1

def grouper_it(n, iterable):
    it = iter(iterable)
    while True:
        chunk_it = itertools.islice(it, n)
        try:
            first_el = next(chunk_it)
        except StopIteration:
            return
        yield itertools.chain((first_el,), chunk_it)

def insert_image(chunk_size, max_results=5000, from_file=None):
    count = 0
    success_count = 0
    es = search.init()
    search.Image.init()
    mapping = search.Image._doc_type.mapping
    mapping.save('openledger')

    for chunk in grouper_it(chunk_size, import_from_file(from_file)):
        if not from_file and count >= max_results:  # Load everything if loading from file
            break
        else:
            images = []
            for result in chunk:
                images.append(result)
            if len(images) > 0:
                try:
                    # Bulk update the search engine too
                    search_objs = [search.db_image_to_index(img).to_dict(include_meta=True) for img in images]
                    models.Image.objects.bulk_create(images)
                    helpers.bulk(es, search_objs)
                    log.debug("*** Committed set of %d images", len(images))
                    success_count += len(images)
                except IntegrityError as e:
                    log.warn("Got one or more integrity errors on batch: %s", e)
                finally:
                    count += len(images)
    return success_count
