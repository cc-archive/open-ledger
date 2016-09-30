import json
import os

import responses

def activate_all_provider_mocks():
    """Mock all the responses we know about from all the providers"""
    activate_500px_mocks()
    activate_rijks_mocks()
    activate_flickr_mocks()
    activate_wikimedia_mocks()

def activate_flickr_mocks():
    from openledger.handlers.handler_flickr import auth
    flickr = auth()
    responses.add(responses.POST, flickr.REST_URL, status=200, content_type='application/json',
                      json=load_json_data('flickr-response.json'))

def activate_500px_mocks():
    from openledger.handlers.handler_500px import ENDPOINT_PHOTOS
    responses.add(responses.GET, ENDPOINT_PHOTOS, status=200, content_type='application/json',
                  json=load_json_data('500px-response.json'))

def activate_rijks_mocks():
    from openledger.handlers.handler_rijks import ENDPOINT_PHOTOS
    responses.add(responses.GET, ENDPOINT_PHOTOS, status=200, content_type='application/json',
                  json=load_json_data('rijks-response.json'))

def activate_wikimedia_mocks():
    from openledger.handlers.handler_wikimedia import BASE_URL, WIKIDATA_URL
    entities_template = load_json_data('wikimedia-entities-response.json')
    wikidata_template = load_json_data('wikimedia-data-response.json')
    responses.add(responses.GET, BASE_URL, status=200, content_type='application/json',
                  json=entities_template)
    responses.add(responses.GET, WIKIDATA_URL, status=200, content_type='application/json',
                  json=wikidata_template)

def load_json_data(datafile):
    """Load testing data in JSON format relative to the path where the test lives"""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    return json.loads(open(os.path.join(dir_path, datafile)).read())
