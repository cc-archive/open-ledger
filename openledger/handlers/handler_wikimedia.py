# encoding: utf-8
import os
import logging
from pprint import pprint
import requests
from string import Template

from openledger import app

log = logging.getLogger(__name__)

BASE_URL = 'https://www.wikidata.org/w/api.php'
WIKIDATA_URL = 'https://query.wikidata.org/sparql'

LIMIT = 20

def auth():
    pass

def photos(search=None):
    params = {
        'search': search,
        'language': 'en',
        'action': 'wbsearchentities',
        'format': 'json',
        'limit': LIMIT,
    }
    r = requests.get(BASE_URL, params).json()
    if r.get('search') and len(r.get('search')) > 0:
        # Take the first representation, as that's likely to be the best
        entity = r.get('search')[0]
        entity_id = entity.get('id')
        image_query_for_entity = image_query.substitute(entity_id=entity_id, limit=LIMIT)
        sparams = {
            'query': image_query_for_entity,
            'format': 'json',
        }
        sr = requests.get(WIKIDATA_URL, sparams)
        results = sr.json()
        return results


# Q146 is the identifier for 'cat', we have to look that up first
# Paris: Q90 (doesn't work as an 'instance of' search, since it's already an entity)
# Properties used: instance of (P31), image (P18)]
# Depicts: P180
image_query = Template("""
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
