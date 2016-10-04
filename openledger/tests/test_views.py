import unittest
import responses

from flask import request

from openledger import app
from openledger.tests.utils import *

class TestViews(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        activate_all_provider_mocks()

    @responses.activate
    def test_index(self):
        """The home page should load without errors"""
        rv = self.app.get('/')
        assert rv

    @responses.activate
    def test_search(self):
        """It should be possible to issue a search and get results lists from all the providers"""
        query = 'test'
        with self.app as c:
            rv = self.app.get('/?search=' + query)
            assert request.args['search'] == query

    def test_openimages(self):
        """The openimages endpoint should load without errors"""
        rv = self.app.get('/source/openimages')
        assert rv
