import unittest
import responses
import flickrapi
import requests

from openledger import app
from openledger.handlers.handler_flickr import photos, auth
from openledger.tests.utils import load_json_data

class HandlerTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.flickr = auth()
        self.template = load_json_data('flickr-response.json')
        responses.add(responses.POST, self.flickr.REST_URL, status=200, content_type='application/json',
                      json=self.template)

    @responses.activate
    def test_flickr_photos(self):
        """The Flickr handler should return a FlickrAPI object when authenticating"""
        resp = photos(search="test")
        assert resp

    @responses.activate
    def test_flickr_response_length(self):
        """The Flickr handler should return the expected number of responses"""
        resp = photos(search="test")
        assert 20 == len(resp['photos']['photo'])

    @responses.activate
    def test_flickr_page(self):
        """The Flickr handler should return the current page of the result set"""
        resp = photos(search="test")
        assert 1 == resp['photos']['page']

    @responses.activate
    def test_flickr_total_pages(self):
        """The Flickr handler should return the total number of pages of the result set"""
        resp = photos(search="test")
        assert '739' == resp['photos']['pages']  # For some reason Flickr gives this as a string, sigh

    @responses.activate
    def test_flickr_total_pages(self):
        """The Flickr handler should return the total number of results"""
        resp = photos(search="test")
        assert '14771' == resp['photos']['total']  # For some reason Flickr gives this as a string, sigh
