# encoding: utf-8
import math
import logging
import os
from pprint import pprint
import requests
from string import Template

from openledger import app

log = logging.getLogger(__name__)

BASE_URL = 'https://www.wikidata.org/w/api.php'
WIKIDATA_URL = 'https://query.wikidata.org/sparql'

LICENSE_VERSION = "1.0"
LICENSE_URL = "https://creativecommons.org/publicdomain/zero/1.0/"

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

def photos(search=None, page=1, per_page=20, **kwargs):
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

SELECT ?item ?itemLabel ?pic
WHERE
{
    # Select either "instance of" (for general categories like animals...)
	{?item wdt:P31 wd:$entity_id .}
    UNION
    # Or "depictions of", as in art
	{?item wdt:P180 wd:$entity_id .}

    # Include the picture in the result set, and that picture is mandatory
    ?item wdt:P18 ?pic

    # From Wikimedia blah blah
	SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }

    # Get the date this is from ...
    OPTIONAL { ?item wdt:P571 ?_inception. }
}
# Then order by it, most recent first (this gives best results)
ORDER BY DESC(?_inception)
LIMIT $limit
""")
