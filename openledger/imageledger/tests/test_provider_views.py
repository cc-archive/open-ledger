import os
import unittest
import responses

from django.test import TestCase, override_settings
from django.urls import reverse
from django.conf import settings

class TestProviderespiews(TestCase):

    @responses.activate
    def test_index(self):
        """The home page should load without errors"""
        resp = self.client.get('/provider-apis')
        assert resp

    @responses.activate
    def test_search(self):
        """It should be possible to issue a search and get results lists from all the providers"""
        query = 'test'
        with self.client as c:
            resp = self.client.get('/provider-apis?search=' + query)
            assert request.args['search'] == query

    @responses.activate
    def test_search_by_provider(self):
        """It should be possible to issue a search and get results lists from a specific provider and no other"""
        query = 'test'
        provider = 'flickr'
        not_provider = '5px'
        url = url_for('by_provider', provider=provider)
        resp = self.client.get(url, query_string={'search': query})
        assert provider in self.get_context_variable('search_data')['providers']
        assert not_provider not in self.get_context_variable('search_data')['providers']

    @responses.activate
    def test_pagination_links_provider(self):
        """The links to paginate among providers should appear and resolve correctly"""
        query = 'test'
        resp = self.client.get('/provider-apis?search=' + query)
        p = select_node(resp, '.pagination-next a')
        assert 'flickr' in p.attrib['href']

    @responses.activate
    def test_pagination_links_license(self):
        """[#41] The links to paginate among providers with license filters should include the license"""
        license = 'CC0'
        query = 'test&licenses=' + license
        resp = self.client.get('/provider-apis?search=' + query)
        p = select_node(resp, '.pagination-next a')
        assert license in p.attrib['href']

    @responses.activate
    def test_unknown_license_ignored(self):
        """[#40] The links to paginate among providers with license filters should include the license"""
        license = 'unknown'
        query = 'test&licenses=' + license
        resp = self.client.get('/provider-apis?search=' + query)
        assert resp.status_code == 200

    @responses.activate
    def test_detail_page_from_provider(self):
        """[#54] It should be possible to follow a link to a detail page from a provider search result"""
        query = 'test'
        resp = self.client.get('/provider-apis?search=' + query)
        p = select_node(resp, '.t-detail-link')
        link = p.attrib['href']
        resp = self.client.get(link)
        assert 200 == resp.status_code
