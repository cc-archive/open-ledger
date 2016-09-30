import unittest
import responses
import requests

from openledger import app
from openledger.handlers.handler_500px import photos, auth, BASE_URL, ENDPOINT_PHOTOS
from openledger.tests.utils import load_json_data

class HandlerTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.template = load_json_data('500px-response.json')
        responses.add(responses.GET, ENDPOINT_PHOTOS, status=200, content_type='application/json',
                      json=self.template)

    @responses.activate
    def test_500px_photos(self):
        """The 500px handler should return a 500px API object when authenticating"""
        resp = photos(search="test")
        assert resp

    @responses.activate
    def test_500px_response_length(self):
        """The 500px handler should return the expected number of responses"""
        resp = photos(search="test")
        assert 20 == len(resp['photos'])

    @responses.activate
    def test_500px_page(self):
        """The 500px handler should return the current page of the result set"""
        resp = photos(search="test")
        assert 1 == resp['current_page']

    @responses.activate
    def test_500px_total_pages(self):
        """The 500px handler should return the total number of pages of the result set"""
        resp = photos(search="test")
        assert 698 == resp['total_pages']

    @responses.activate
    def test_500px_total_results(self):
        """The 500px handler should return the total number of results"""
        resp = photos(search="test")
        assert 13949 == resp['total_items']
