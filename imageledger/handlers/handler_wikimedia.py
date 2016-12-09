# encoding: utf-8
import math
import logging
import os
from pprint import pprint
import requests
from string import Template

from django.utils import timezone

log = logging.getLogger(__name__)

BASE_URL = 'https://www.wikidata.org/w/api.php'
WIKIDATA_URL = 'https://query.wikidata.org/sparql'

PROVIDER_NAME = 'wikimedia'
SOURCE_NAME = 'wikimedia'

LICENSE_VERSION = "1.0"
LICENSE_URL = "https://creativecommons.org/publicdomain/zero/1.0/"

from imageledger.handlers.utils import *

# TODO: Cache these results since we're paginating ourselves
MAX_LIMIT = 100  # The total number of results we'll ever ask for

def auth():
    pass

def entity_search(search):
    """Identify a particular Wikidata entity for a given search query"""
    params = {
        'search': search,
        'language': 'en',
        'action': 'wbsearchentities',
        'format': 'json',
        'limit': 1,  # May want to change that if we want to expand the entity space
    }
    r = requests.get(BASE_URL, params)
    return r.json()

def prepare_sparql_query(entity_id, limit):
    return image_query.substitute(entity_id=entity_id, limit=MAX_LIMIT)

def photos(search=None, page=1, per_page=200, **kwargs):
    r = entity_search(search)
    if r.get('search') and len(r.get('search')) > 0:
        # Take the first representation, as that's likely to be the best
        entity = r.get('search')[0]
        entity_id = entity.get('id')
        image_query_for_entity = prepare_sparql_query(entity_id=entity_id, limit=MAX_LIMIT)

        sparams = {
            'query': image_query_for_entity,
            'format': 'json',
        }
        sr = requests.get(WIKIDATA_URL, sparams)
        # We have to do pagination ourselves, whee
        offset = (int(page) - 1) * int(per_page)
        results = {'results': sr.json()['results']['bindings']}
        results['page'] = int(page)
        results['total'] = len(results['results'])
        results['pages'] = math.ceil(results['total']/ per_page)
        results['results'] = results['results'][offset:offset + per_page]
        return results

def walk(page=1, per_page=100):
    """Walk through a set of search results and collect items to serialize"""

    has_more = True
    while has_more:
        for tag in models.Tag.objects.all():
            log.debug("Searching for results for tag %s", tag.name)
            results = photos(search=tag.name, page=page, per_page=per_page)
            if results:
                for result in results['results']:
                    yield result
                time.sleep(2)

def serialize(result):
    url = result['pic']['value']
    thumbnail = url
    image = models.Image(url=url)
    image.provider = PROVIDER_NAME
    image.source = SOURCE_NAME
    if not result.get('creatorLabel'):
        return
    image.creator = result['creatorLabel']['value']
    image.license = "CC0"
    image.license_version = "1.0"
    image.foreign_landing_url = result['item']['value']
    image.foreign_identifer = result['itemLabel']['value']
    image.title = result['itemLabel']['value']
    if result.get('creator') and result['creator']['type'] == 'uri':
        image.creator_url = result['creator']['value']
    image.identifier = signals.create_identifier(image.url)
    image.last_synced_with_source = timezone.now()
    log.debug("Returning image with url %s", url)
    return image

# Q146 is the identifier for 'cat', we have to look that up first
# Paris: Q90 (doesn't work as an 'instance of' search, since it's already an entity)
# Properties used: instance of (P31), image (P18)]
# Depicts: P180
image_query = Template("""
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX bd: <http://www.bigdata.com/rdf#>

SELECT ?item ?itemLabel ?creatorLabel ?pic ?creator
WHERE
{
    # Select either "instance of" (for general categories like animals...)
	#{?item wdt:P31 wd:$entity_id .}
    #UNION
    # Or "depictions of", as in art
	{?item wdt:P180 wd:$entity_id .}

    # Include the picture in the result set, and that picture is mandatory
    ?item wdt:P18 ?pic

    # From Wikimedia blah blah
	SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }

    # Get the date this is from ...
    OPTIONAL { ?item wdt:P571 ?_inception. }

    # Creator, optional
    OPTIONAL { ?item wdt:P170 ?creator}

}
# Then order by it, most recent first (this gives best results)
ORDER BY DESC(?_inception)
LIMIT $limit
""")
