import os
import unittest
import responses
import jinja2
from flask_testing import TestCase

from flask import request, url_for

from openledger import app as ol
from openledger.tests.utils import *

class TestViews(TestCase):

    def create_app(self):
        app = ol
        app.config['TESTING'] = True
        # Be defensive in our tests about undefined variables
        app.jinja_env.undefined = jinja2.StrictUndefined
        return app

    def setUp(self):
        activate_all_provider_mocks()

    @responses.activate
    def test_index(self):
        """The home page should load without errors"""
        rv = self.client.get('/')
        assert rv

    @responses.activate
    def test_search(self):
        """It should be possible to issue a search and get results lists from all the providers"""
        query = 'test'
        with self.client as c:
            rv = self.client.get('/?search=' + query)
            assert request.args['search'] == query

    @responses.activate
    def test_search_by_provider(self):
        """It should be possible to issue a search and get results lists from a specific provider and no other"""
        query = 'test'
        provider = 'flickr'
        not_provider = '5px'
        url = url_for('by_provider', provider=provider)
        rv = self.client.get(url, query_string={'search': query})
        assert provider in self.get_context_variable('search_data')['providers']
        assert not_provider not in self.get_context_variable('search_data')['providers']

    @responses.activate
    def test_pagination_links_provider(self):
        """The links to paginate among providers should appear and resolve correctly"""
        query = 'test'
        rv = self.client.get('/?search=' + query)
        p = select_node(rv, '.pagination-next a')
        assert 'flickr' in p.attrib['href']

    @responses.activate
    def test_pagination_links_license(self):
        """[#41] The links to paginate among providers with license filters should include the license"""
        license = 'CC0'
        query = 'test&licenses=' + license
        rv = self.client.get('/?search=' + query)
        p = select_node(rv, '.pagination-next a')
        assert license in p.attrib['href']

    @responses.activate
    def test_unknown_license_ignored(self):
        """[#40] The links to paginate among providers with license filters should include the license"""
        license = 'unknown'
        query = 'test&licenses=' + license
        rv = self.client.get('/?search=' + query)
        assert rv.status_code == 200
        p = select_node(rv, 'body')

    def test_openimages(self):
        """The openimages endpoint should load without errors"""
        rv = self.client.get('/source/openimages')
        assert rv
