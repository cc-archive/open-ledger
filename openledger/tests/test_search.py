import logging
import os
import time

from elasticsearch import Elasticsearch
from elasticsearch.client import ClusterClient
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.connections import connections
from flask import request, url_for
import pytest
from testing.elasticsearch import ElasticSearchServer

from openledger import app as ol
from openledger import search
from openledger.tests.utils import *

console = logging.StreamHandler()
log = logging.getLogger(__name__)
log.addHandler(console)
log.setLevel(logging.DEBUG)

MAX_RETRIES = 5

@pytest.fixture(scope='class')
def elasticsearch(request):
    test_es = ElasticSearchServer(config={
#        'logger.level': 'DEBUG',
        'index.store.type': 'mmapfs',
        'index.number_of_shards': 1,
        'index.number_of_replicas': 0,
    })
    test_es.start()
    request.addfinalizer(test_es.stop)
    request.cls.test_es = test_es

@pytest.mark.usefixtures("elasticsearch")
class TestSearch(TestOpenLedgerApp):

    def setUp(self):
        super().setUp()
        es = Elasticsearch(host=self.test_es._bind_host,
                           port=self.test_es._bind_port,
                           max_retries=5)
        connections.add_connection('default', es)
        self.es = es
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
        self.add_to_db(self.img1, self.img2)
        self.url = url_for('fulltext')

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
        url = url_for('fulltext')
        rv = self.client.get(url)
        assert 200 == rv.status_code

    def test_search_no_results(self):
        """It should be possible to get a no-results page"""
        rv = self.client.get(self.url, query_string={'search': 'nothing'})
        p = select_node(rv, '.t-no-results')
        assert p is not ()

    def test_search_results(self):
        """If indexed, a single result should be returned from the search engine"""
        self._index_img(self.img1)
        rv = self.client.get(self.url, query_string={'search': 'greyhounds'})
        p = select_nodes(rv, '.t-image-result')
        assert 1 == len(p)
        assert select_node(rv, '.t-no-results') is ()


    def test_search_filter_creator(self):
        """It should be possible to filter search results by creator"""
        self._index_img(self.img1)
        self._index_img(self.img2)
        rv = self.client.get(self.url, query_string={'search_fields': 'creator', 'search': '諸葛亮'})
        assert select_node(rv, '.t-no-results') is ()
        assert 1 == len(select_nodes(rv, '.t-image-result'))

        # Should not find it when searching the title field
        rv = self.client.get(self.url, query_string={'search_fields': 'title', 'search': '諸葛亮'})
        assert select_node(rv, '.t-no-results') is not ()

    def test_search_filter_title(self):
        """It should be possible to filter search results by title"""
        self._index_img(self.img1)
        self._index_img(self.img2)
        rv = self.client.get(self.url, query_string={'search_fields': 'title', 'search': 'orange'})
        assert select_node(rv, '.t-no-results') is ()
        assert 1 == len(select_nodes(rv, '.t-image-result'))

        # Should not find it when searching the creator field
        rv = self.client.get(self.url, query_string={'search_fields': 'creator', 'search': 'orange'})
        assert select_node(rv, '.t-no-results') is not ()

    def test_search_filter_tags(self):
        """It should be possible to filter search results by tags"""
        self._index_img(self.img1)
        self._index_img(self.img2)
        rv = self.client.get(self.url, query_string={'search_fields': 'tags', 'search': 'dog', 'work_types': ''})
        assert select_node(rv, '.t-no-results') is ()
        assert 1 == len(select_nodes(rv, '.t-image-result'))

        # Should not find it when searching the creator field
        rv = self.client.get(self.url, query_string={'search_fields': 'creator', 'search': 'dog', 'work_types': ''})
        assert select_node(rv, '.t-no-results') is not ()

        # Find both with the same tag
        rv = self.client.get(self.url, query_string={'search_fields': 'tags', 'search': 'object', 'work_types': ''})
        assert select_node(rv, '.t-no-results') is ()
        assert 2 == len(select_nodes(rv, '.t-image-result'))

    def test_works_filter(self):
        """It should be possible to filter by work_type"""
        self._index_img(self.img1)
        self._index_img(self.img2)
        rv = self.client.get(self.url, query_string={'search': 'object', 'work_types': 'photos'})
        assert 1 == len(select_nodes(rv, '.t-image-result'))

        rv = self.client.get(self.url, query_string={'search': 'object', 'work_types': 'cultural'})
        assert 1 == len(select_nodes(rv, '.t-image-result'))

        rv = self.client.get(self.url, query_string={'search': 'object', 'work_types': 'unknown'})
        assert 2 == len(select_nodes(rv, '.t-image-result'))
