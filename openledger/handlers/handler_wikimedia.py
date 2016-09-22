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

def auth():
    pass

def photos(search=None):
    params = {
        'search': search,
        'language': 'en',
        'action': 'wbsearchentities',
        'format': 'json',
    }
    r = requests.get(BASE_URL, params).json()
    if r.get('search') and len(r.get('search')) > 0:
        # Take the first representation, as that's likely to be the best
        entity = r.get('search')[0]
        entity_id = entity.get('id')
        image_query_for_entity = image_query.substitute(entity_id=entity_id)
        sparams = {
            'query': image_query_for_entity,
            'format': 'json'
        }
        sr = requests.get(WIKIDATA_URL, sparams)
        results = sr.json()['results']['bindings']
        pprint(results[2])
    pass



# Q___ is the identifier for 'cat'
# How do we get that?
# Properties used: instance of (P31), image (P18)
image_query = Template("""
SELECT ?item ?itemLabel ?pic
WHERE
{
	?item wdt:P31 wd:$entity_id .
	OPTIONAL {
		?item wdt:P18 ?pic
	}
	SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
}
""")
