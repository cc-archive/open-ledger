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
from testing.elasticsearch import ElasticSearchServer
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

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.search_server = ElasticSearchServer(config={
            'logger.level': 'ERROR',
            'index.store.type': 'mmapfs',
            'index.number_of_shards': 1,
            'index.number_of_replicas': 0,
        })
        cls.search_server.start()
        cls.es_host = cls.search_server._bind_host
        cls.es_port = cls.search_server._bind_port

    @classmethod
    def tearDownClass(cls):
        cls.search_server.stop()

    def setUp(self):
        super().setUp()
        with self.settings(ELASTICSEARCH_URL=TestSearch.es_host,
                           ELASTICSEARCH_PORT=TestSearch.es_port):

                           self.es = search.init_es()
                           connections.add_connection('default', self.es)
                           self.s = Search()

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
        index = Index('openledger')
        index.delete(ignore=404)

    def _index_img(self, img):
        """Index a single img and ensure that it's been propagated to the search engine"""
        search.Image.init()
        image = search.db_image_to_index(img)
        image.save()
        self.es.indices.refresh(force=True)

    def test_query(self):
        """It should be possible to query the search engine for results"""
        q = Q("match", title="greyhounds")
        s = self.s.query(q)
        r = s.execute()
        assert 0 == r.hits.total  # We haven't indexed anything, so no results are expected

    def test_store(self):
        """It should be possible to index a database item"""
        search.Image.init()
        image = search.db_image_to_index(self.img1)
        image.save()

    def test_retrieve(self):
        """It should be possible to retrieve a database item by auto-id"""
        search.Image.init()
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
        assert 1 == r.hits.total

    def test_search_view(self):
        """It should be possible to load the search view"""
        resp = self.client.get(self.url)
        assert 200 == resp.status_code

    def test_search_no_results(self):
        """It should be possible to get a no-results page"""

        resp = self.client.get(self.url, {'search': 'nothing'})
        p = select_node(resp, '.t-no-results')
        assert p is not ()

    def test_search_results(self):
        """If indexed, a single result should be returned from the search engine"""
        self._index_img(self.img1)
        resp = self.client.get(self.url, {'search': 'greyhounds', 'search_fields': 'title'})
        p = select_nodes(resp, '.t-image-result')
        assert 1 == len(p)
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
        resp = self.client.get(self.url, {'search': 'object', 'work_types': 'photos'})
        assert 1 == len(select_nodes(resp, '.t-image-result'))

        resp = self.client.get(self.url, {'search': 'object', 'work_types': 'cultural'})
        assert 1 == len(select_nodes(resp, '.t-image-result'))

    def test_remove_from_search_after_sync(self):
        """When an image is removed from the source, it should be removed from the search engine"""
        self._index_img(self.removed)
        s = self.s.query(Q("match", title="removed"))
        r = s.execute()
        assert 1 == r.hits.total
        with responses.RequestsMock() as rsps:
            rsps.add(responses.HEAD, FOREIGN_URL + TEST_IMAGE_REMOVED, status=404)
            self.removed.sync()
        signals._update_search_index(self.removed)
        self.es.indices.refresh(force=True)
        s = self.s.query(Q("match", title="removed"))
        r = s.execute()
        assert 0 == r.hits.total
