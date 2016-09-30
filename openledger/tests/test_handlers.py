import unittest
import responses
import flickrapi
import requests

from openledger import app
from openledger.handlers.handler_500px import photos as search_500
from openledger.handlers.handler_rijks import photos as search_rijks
from openledger.handlers.handler_flickr import photos as search_flickr
from openledger.handlers.handler_wikimedia import photos as search_wikimedia

from openledger.tests.utils import load_json_data

class FlickrTestCase(unittest.TestCase):
    def setUp(self):
        from openledger.handlers.handler_flickr import auth
        app.config['TESTING'] = True
        self.flickr = auth()
        self.template = load_json_data('flickr-response.json')
        responses.add(responses.POST, self.flickr.REST_URL, status=200, content_type='application/json',
                      json=self.template)

    @responses.activate
    def test_flickr_search(self):
        """The Flickr handler should return a FlickrAPI object when authenticating"""
        resp = search_flickr(search="test")
        assert resp

    @responses.activate
    def test_flickr_response_length(self):
        """The Flickr handler should return the expected number of responses"""
        resp = search_flickr(search="test")
        assert 20 == len(resp['photos']['photo'])

    @responses.activate
    def test_flickr_page(self):
        """The Flickr handler should return the current page of the result set"""
        resp = search_flickr(search="test")
        assert 1 == resp['photos']['page']

    @responses.activate
    def test_flickr_total_pages(self):
        """The Flickr handler should return the total number of pages of the result set"""
        resp = search_flickr(search="test")
        assert '739' == resp['photos']['pages']  # For some reason Flickr gives this as a string, sigh

    @responses.activate
    def test_flickr_total_results(self):
        """The Flickr handler should return the total number of results"""
        resp = search_flickr(search="test")
        assert '14771' == resp['photos']['total']  # For some reason Flickr gives this as a string, sigh


class FiveHundredPixelsTestCase(unittest.TestCase):
    def setUp(self):
        from openledger.handlers.handler_500px import ENDPOINT_PHOTOS
        app.config['TESTING'] = True
        self.template = load_json_data('500px-response.json')
        responses.add(responses.GET, ENDPOINT_PHOTOS, status=200, content_type='application/json',
                      json=self.template)

    @responses.activate
    def test_500px_photos(self):
        """The 500px handler should return a 500px API object when authenticating"""
        resp = search_500(search="test")
        assert resp

    @responses.activate
    def test_500px_response_length(self):
        """The 500px handler should return the expected number of responses"""
        resp = search_500(search="test")
        assert 20 == len(resp['photos'])

    @responses.activate
    def test_500px_page(self):
        """The 500px handler should return the current page of the result set"""
        resp = search_500(search="test")
        assert 1 == resp['current_page']

    @responses.activate
    def test_500px_total_pages(self):
        """The 500px handler should return the total number of pages of the result set"""
        resp = search_500(search="test")
        assert 698 == resp['total_pages']

    @responses.activate
    def test_500px_total_results(self):
        """The 500px handler should return the total number of results"""
        resp = search_500(search="test")
        assert 13949 == resp['total_items']


class RijksTestCase(unittest.TestCase):
    def setUp(self):
        from openledger.handlers.handler_rijks import ENDPOINT_PHOTOS
        app.config['TESTING'] = True
        self.template = load_json_data('rijks-response.json')
        responses.add(responses.GET, ENDPOINT_PHOTOS, status=200, content_type='application/json',
                      json=self.template)

    @responses.activate
    def test_rijks_search(self):
        """The rijks handler should return a rijks API object when authenticating"""
        resp = search_rijks(search="test")
        assert resp

    @responses.activate
    def test_rijks_response_length(self):
        """The rijks handler should return the expected number of responses"""
        resp = search_rijks(search="test")
        assert 20 == len(resp['artObjects'])

    @responses.activate
    def test_rijks_page(self):
        """The rijks handler should return the current page of the result set"""
        resp = search_rijks(search="test")
        assert 1 == resp['page']

    @responses.activate
    def test_rijks_total_pages(self):
        """The rijks handler should return the total number of pages of the result set"""
        resp = search_rijks(search="test")
        assert 274 == resp['pages']

    @responses.activate
    def test_rijks_total_results(self):
        """The rijks handler should return the total number of results"""
        resp = search_rijks(search="test")
        assert 5489 == resp['count']

class WikimediaTestCase(unittest.TestCase):
    def setUp(self):
        from openledger.handlers.handler_wikimedia import BASE_URL, WIKIDATA_URL
        app.config['TESTING'] = True
        self.entities_template = load_json_data('wikimedia-entities-response.json')
        self.wikidata_template = load_json_data('wikimedia-data-response.json')
        responses.add(responses.GET, BASE_URL, status=200, content_type='application/json',
                      json=self.entities_template)
        responses.add(responses.GET, WIKIDATA_URL, status=200, content_type='application/json',
                      json=self.wikidata_template)

    @responses.activate
    def test_wikimedia_entity(self):
        """The wikimedia handler should return an entity response to a text query"""
        from openledger.handlers.handler_wikimedia import entity_search
        resp = entity_search(search="test")
        assert 1 == len(resp.get('search'))

    @responses.activate
    def test_wikimedia_response_length(self):
        """The wikimedia handler should return the expected number of responses"""
        resp = search_wikimedia(search="test")
        assert 9 == len(resp['results'])

    @responses.activate
    def test_wikimedia_page(self):
        """The wikimedia handler should return the current page of the result set"""
        resp = search_wikimedia(search="test")
        assert 1 == resp['page']

    @responses.activate
    def test_wikimedia_total_pages(self):
        """The wikimedia handler should return the total number of pages of the result set"""
        resp = search_wikimedia(search="test")
        assert 1 == resp['pages']

    @responses.activate
    def test_wikimedia_total_results(self):
        """The wikimedia handler should return the total number of results"""
        resp = search_wikimedia(search="test")
        assert 9 == resp['total']

    def test_wikimedia_sparql(self):
        """The SPARQL construction method should return a valid SPARQL statement"""
        from rdflib.plugins.sparql import prepareQuery
        from openledger.handlers.handler_wikimedia import prepare_sparql_query
        q = prepareQuery(prepare_sparql_query("W30", 100))
        assert q  # This should parse successfully

        
