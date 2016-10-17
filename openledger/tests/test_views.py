import unittest
import responses
from lxml.html import tostring, html5parser
import html5lib
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

    @responses.activate
    def test_pagination_links_provider(self):
        """The links to paginate among providers should appear and resolve correctly"""
        query = 'test'
        with self.app as c:
            rv = self.app.get('/?search=' + query)
            h = html5lib.parse(rv.data.decode('utf-8'), treebuilder='lxml', namespaceHTMLElements=False)
            p = h.getroot().cssselect('.pagination-next a')[0]
            assert 'flickr' in p.attrib['href']

    @responses.activate
    def test_pagination_links_license(self):
        """The links to paginate among providers with license filters should include the license"""
        license = 'CC0'
        query = 'test&licenses=CC0'
        with self.app as c:
            rv = self.app.get('/?search=' + query)
            h = html5lib.parse(rv.data.decode('utf-8'), treebuilder='lxml', namespaceHTMLElements=False)
            p = h.getroot().cssselect('.pagination-next a')[0]
            assert license in p.attrib['href']



    def test_openimages(self):
        """The openimages endpoint should load without errors"""
        rv = self.app.get('/source/openimages')
        assert rv
