import os
import unittest
import responses

import jinja2
from flask import request

from openledger import app
from openledger.tests.utils import *

class TestViews(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        activate_all_provider_mocks()
        # Be defensive in our tests about undefined variables
        app.jinja_env.undefined = jinja2.StrictUndefined

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

    @responses.activate
    def test_pagination_links_provider(self):
        """The links to paginate among providers should appear and resolve correctly"""
        query = 'test'
        with self.app as c:
            rv = self.app.get('/?search=' + query)
            p = select_node(rv, '.pagination-next a')
            assert 'flickr' in p.attrib['href']

    @responses.activate
    def test_pagination_links_license(self):
        """[#41] The links to paginate among providers with license filters should include the license"""
        license = 'CC0'
        query = 'test&licenses=' + license
        with self.app as c:
            rv = self.app.get('/?search=' + query)
            p = select_node(rv, '.pagination-next a')
            assert license in p.attrib['href']

    @responses.activate
    def test_unknown_license_ignored(self):
        """[#40] The links to paginate among providers with license filters should include the license"""
        license = 'unknown'
        query = 'test&licenses=' + license
        with self.app as c:
            rv = self.app.get('/?search=' + query)
            assert rv.status_code == 200
            p = select_node(rv, 'body')

    def test_openimages(self):
        """The openimages endpoint should load without errors"""
        rv = self.app.get('/source/openimages')
        assert rv
