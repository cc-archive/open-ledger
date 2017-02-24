import logging
import os
import time

from django.test import TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch.client import ClusterClient
from elasticsearch_dsl import Search, Q, Index
from elasticsearch_dsl.connections import connections
import responses

from imageledger import search, forms, signals
from imageledger.tests.utils import *

log = logging.getLogger(__name__)

TEST_IMAGE_REMOVED = '404.png'
FOREIGN_URL = 'http://example.com/'

dir_path = os.path.dirname(os.path.realpath(__file__))

MAX_RETRIES = 5

class TestSearch(TestCase):

    es_host = None
    es_port = None

    def setUp(self):
        super().setUp()
        self.es = search.init_es()
        connections.add_connection('default', self.es)
        self.s = Search(index=settings.ELASTICSEARCH_INDEX)
        search.Image.init()

        self.es.cluster.health(wait_for_status='yellow', request_timeout=2000)
        self.img1 = models.Image(title='greyhounds are fast',
                                 creator="Rashid",
                                 url='http://example.com/1',
                                 license='CC0',
                                 provider="flickr",
                                 source="openimages",
                                 tags_list=['greyhound', 'dog', 'object'])
        self.img2 = models.Image(title='pumpkins are orange',
                                 creator='諸葛亮',
                                 url='http://example.com/2',
                                 license='CC-BY',
                                 provider="rijksmuseum",
                                 source="rijksmuseum",
                                 tags_list=['gourds', 'fruit', 'object'])
        self.img1.save()
        self.img2.save()
        self.url = reverse('index')
        self.removed = models.Image.objects.create(title='removed', url=FOREIGN_URL + TEST_IMAGE_REMOVED, license="cc0")


    def tearDown(self):
        index = Index(settings.ELASTICSEARCH_INDEX)
        index.delete(ignore=404)

    def _index_img(self, img):
        """Index a single img and ensure that it's been propagated to the search engine"""
        image = search.db_image_to_index(img)
        image.save()
        self.es.indices.refresh(force=True)

    def test_query(self):
        """It should be possible to query the search engine for results"""
        q = Q("match", title="greyhounds")
        s = self.s.query(q)
        r = s.execute()
        self.assertEqual(0, r.hits.total)  # We haven't indexed anything, so no results are expected

    def test_store(self):
        """It should be possible to index a database item"""
        image = search.db_image_to_index(self.img1)
        image.save()

    def test_retrieve(self):
        """It should be possible to retrieve a database item by auto-id"""
        image = search.db_image_to_index(self.img1)
        image.save()
        id_ = image.meta.id
        image2 = search.Image.get(id=id_)
        assert image2.meta.id == id_

    def test_search(self):
        """It should be possible to find an item by query"""
        self._index_img(self.img1)
        s = self.s.query(Q("match", title="greyhounds"))
        r = s.execute()
        self.assertEquals(1, r.hits.total)

    def test_search_view(self):
        """It should be possible to load the search view"""
        resp = self.client.get(self.url)
        assert 200 == resp.status_code

    def test_search_no_results(self):
        """It should be possible to get a no-results page"""
        resp = self.client.get(self.url, {'search': 'nothing', 'search_fields': 'title'})
        p = select_node(resp, '.t-no-results')
        assert p is not None

    def test_search_results(self):
        """If indexed, a single result should be returned from the search engine"""
        self._index_img(self.img1)
        resp = self.client.get(self.url, {'search': 'greyhounds', 'search_fields': 'title'})
        p = select_nodes(resp, '.t-image-result')
        self.assertEquals(1, len(p))
        assert select_node(resp, '.t-no-results') is None


    def test_search_filter_creator(self):
        """It should be possible to filter search results by creator"""
        self._index_img(self.img1)
        self._index_img(self.img2)
        resp = self.client.get(self.url, {'search_fields': 'creator', 'search': '諸葛亮'})
        assert select_node(resp, '.t-no-results') is None
        self.assertEquals(1, len(select_nodes(resp, '.t-image-result')))

        # Should not find it when searching the title field
        resp = self.client.get(self.url, {'search_fields': 'title', 'search': '諸葛亮'})
        assert select_node(resp, '.t-no-results') is not ()

    def test_search_filter_title(self):
        """It should be possible to filter search results by title"""
        self._index_img(self.img1)
        self._index_img(self.img2)
        resp = self.client.get(self.url, {'search_fields': 'title', 'search': 'orange'})
        assert select_node(resp, '.t-no-results') is None
        assert 1 == len(select_nodes(resp, '.t-image-result'))

        # Should not find it when searching the creator field
        resp = self.client.get(self.url, {'search_fields': 'creator', 'search': 'orange'})
        assert select_node(resp, '.t-no-results') is not ()

    def test_search_filter_tags(self):
        """It should be possible to filter search results by tags"""
        self._index_img(self.img1)
        self._index_img(self.img2)
        resp = self.client.get(self.url, {'search_fields': 'tags', 'search': 'dog'})
        assert select_node(resp, '.t-no-results') is None
        self.assertEqual(1, len(select_nodes(resp, '.t-image-result')))

        # Should not find it when searching the creator field
        resp = self.client.get(self.url, {'search_fields': 'creator', 'search': 'dog'})
        assert select_node(resp, '.t-no-results') is not ()

        # Find both with the same tag
        resp = self.client.get(self.url, {'search_fields': 'tags', 'search': 'object'})
        assert select_node(resp, '.t-no-results') is None
        self.assertEqual(2, len(select_nodes(resp, '.t-image-result')))

    def test_works_filter(self):
        """It should be possible to filter by work_type"""
        self._index_img(self.img1)
        self._index_img(self.img2)
        resp = self.client.get(self.url, {'search': 'object', 'work_types': 'photos', 'search_fields': 'tags'})
        assert 1 == len(select_nodes(resp, '.t-image-result'))

        resp = self.client.get(self.url, {'search': 'object', 'work_types': 'cultural', 'search_fields': 'tags'})
        assert 1 == len(select_nodes(resp, '.t-image-result'))

    def test_remove_from_search_after_sync(self):
        """When an image is removed from the source, it should be removed from the search engine"""
        self._index_img(self.removed)
        s = self.s.query(Q("match", title="removed"))
        r = s.execute()
        self.assertEquals(1, r.hits.total)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.HEAD, FOREIGN_URL + TEST_IMAGE_REMOVED, status=404)
            self.removed.sync()
        signals._update_search_index(self.removed)
        self.es.indices.refresh(force=True)
        s = self.s.query(Q("match", title="removed"))
        r = s.execute()
        self.assertEquals(0, r.hits.total)

    def test_search_with_punctuation(self):
        """[#39] Searches with punctuation should not error"""
        self._index_img(self.img1)
        resp = self.client.get(self.url, {'search': 'A+', 'search_fields': 'title'})
        self.assertEqual(200, resp.status_code)
        p = select_node(resp, '.t-no-results')
        assert p is not None

    def test_provider_selector_no_provider(self):
        """[#122] All results should be returned if no providers are selected"""
        img1 = models.Image.objects.create(url='example.com/1', title='hello', provider='flickr')
        img2 = models.Image.objects.create(url='example.com/2', title='hello', provider='nypl')
        self._index_img(img1)
        self._index_img(img2)
        resp = self.client.get(self.url, {'search_fields': 'title', 'search': 'hello'})
        # Two results
        self.assertEqual(2, len(select_nodes(resp, '.t-image-result')))
        self.assertEqual(1, len(select_nodes(resp, '[data-identifier="' + img1.identifier + '"]')))
        self.assertEqual(1, len(select_nodes(resp, '[data-identifier="' + img2.identifier + '"]')))

    def test_provider_selector_with_provider(self):
        """[#122] Filtering by providers should return only results from that provider"""
        img1 = models.Image.objects.create(url='example.com/1', title='hello', provider='flickr')
        img2 = models.Image.objects.create(url='example.com/2', title='hello', provider='nypl')
        self._index_img(img1)
        self._index_img(img2)
        resp = self.client.get(self.url, {'search_fields': 'title', 'search': 'hello', 'providers': 'flickr'})
        # One result, the correct one
        self.assertEqual(1, len(select_nodes(resp, '.t-image-result')))
        self.assertEqual(1, len(select_nodes(resp, '[data-identifier="' + img1.identifier +'"]')))
        self.assertEqual(0, len(select_nodes(resp, '[data-identifier="' + img2.identifier +'"]')))

    def test_work_types_dont_override_provider(self):
        """[#122] Selecting work types should be a subset of providers, not override them"""
        img1 = models.Image.objects.create(url='example.com/1', title='hello', provider='flickr')
        img2 = models.Image.objects.create(url='example.com/2', title='hello', provider='nypl')
        self._index_img(img1)
        self._index_img(img2)

        # Search by provider=flickr but work type=cultural should limit by Flickr first
        resp = self.client.get(self.url, {'search_fields': 'title',
                                          'search': 'hello',
                                          'providers': 'flickr',
                                          'work_types': 'cultural'})

        # One result, the correct one
        self.assertEqual(1, len(select_nodes(resp, '.t-image-result')))
        self.assertEqual(1, len(select_nodes(resp, '[data-identifier="' + img1.identifier +'"]')))
        self.assertEqual(0, len(select_nodes(resp, '[data-identifier="' + img2.identifier +'"]')))

    def test_sorting(self):
        """[#119] Results should be return in relevance order, always"""
        img1 = models.Image.objects.create(url='example.com/1', title='relevant ' * 10,)
        img2 = models.Image.objects.create(url='example.com/2', title='less ' * 10 + 'relevant',)
        img3 = models.Image.objects.create(url='example.com/3', title='less ' * 100 + 'relevant',)
        img4 = models.Image.objects.create(url='example.com/4', title='not at all rel',)
        self._index_img(img1)
        self._index_img(img2)
        self._index_img(img3)
        self._index_img(img4)
        resp = self.client.get(self.url, {'search_fields': 'title',
                                          'search': 'relevant',})
        self.assertEqual(3, len(select_nodes(resp, '.t-image-result')))
        self.assertEqual(img1.identifier, select_nodes(resp, '.t-image-result')[0].attrib['data-identifier'])
        self.assertEqual(img2.identifier, select_nodes(resp, '.t-image-result')[1].attrib['data-identifier'])
        self.assertEqual(img3.identifier, select_nodes(resp, '.t-image-result')[2].attrib['data-identifier'])

    def test_results_dont_repeat(self):
        """[#119] Results on page 1 should not reappear on page 2"""
        # Re-set the results per page (this could be less fragile)
        prev_default = forms.RESULTS_PER_PAGE_DEFAULT
        forms.RESULTS_PER_PAGE_DEFAULT = 2

        img1 = models.Image.objects.create(url='example.com/1', title='relevant ' * 10,)
        img2 = models.Image.objects.create(url='example.com/2', title='less ' * 10 + 'relevant',)
        img3 = models.Image.objects.create(url='example.com/3', title='less ' * 100 + 'relevant',)
        img4 = models.Image.objects.create(url='example.com/4', title='less ' * 200 + 'relevant',)
        self._index_img(img1)
        self._index_img(img2)
        self._index_img(img3)
        self._index_img(img4)
        resp = self.client.get(self.url, {'search_fields': 'title',
                                          'search': 'relevant',})
        # Page 1 should only have 2 results
        self.assertEqual(2, len(select_nodes(resp, '.t-image-result')))
        self.assertEqual(img1.identifier, select_nodes(resp, '.t-image-result')[0].attrib['data-identifier'])
        self.assertEqual(img2.identifier, select_nodes(resp, '.t-image-result')[1].attrib['data-identifier'])

        # Page 2 should have 2 results as well, but the other 2
        resp = self.client.get(self.url, {'search_fields': 'title',
                                          'search': 'relevant',
                                          'page': 2})

        self.assertEqual(2, len(select_nodes(resp, '.t-image-result')))
        self.assertEqual(img3.identifier, select_nodes(resp, '.t-image-result')[0].attrib['data-identifier'])
        self.assertEqual(img4.identifier, select_nodes(resp, '.t-image-result')[1].attrib['data-identifier'])
        forms.RESULTS_PER_PAGE_DEFAULT = prev_default

    def test_license_types(self):
        """[#123] Allow selection by license type"""
        img1 = models.Image.objects.create(url='example.com/1',
                                           title='licensetest nc',
                                           license='by-nc',
                                           provider='nypl')
        img2 = models.Image.objects.create(url='example.com/2',
                                           title='licensetest by',
                                           license='by',
                                           provider='flickr')
        img3 = models.Image.objects.create(url='example.com/3',
                                           title='licensetest nd',
                                           license='by-nd',
                                           provider='flickr')
        self._index_img(img1)
        self._index_img(img2)
        self._index_img(img3)
        resp = self.client.get(self.url, {'search_fields': 'title',
                                          'search': 'licensetest',})
        self.assertEqual(3, len(select_nodes(resp, '.t-image-result')))
        resp = self.client.get(self.url, {'search_fields': 'title',
                                          'search': 'licensetest',
                                          'licenses': ['ALL-$']})
        self.assertEqual(2, len(select_nodes(resp, '.t-image-result')))
        resp = self.client.get(self.url, {'search_fields': 'title',
                                          'search': 'licensetest',
                                          'licenses': ['ALL-MOD']})
        self.assertEqual(2, len(select_nodes(resp, '.t-image-result')))

    def test_custom_provider_view(self):
        """[#156] Test that provider view with a custom URL works"""
        img1 = models.Image.objects.create(url='example.com/1',
                                           title='other result',
                                           license='by-nc',
                                           provider='nypl')
        img2 = models.Image.objects.create(url='example.com/2',
                                           title='met result',
                                           license='by',
                                           provider='met')
        self._index_img(img1)
        self._index_img(img2)

        # The GET request should redirect
        resp = self.client.get(reverse('search-met'))
        self.assertEquals(resp.status_code, 301)
