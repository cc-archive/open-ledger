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
        self.img1 = models.Image(title='greyhounds are fast', creator="Rashid", url='http://example.com/1', license='CC0')
        self.img2 = models.Image(title='pumpkins are orange', creator='諸葛亮', url='http://example.com/2', license='CC-BY')
        self.add_to_db(self.img1, self.img2)

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
        search.Image.init()
        image = search.db_image_to_index(self.img1)
        image.save()
        self.es.indices.refresh(force=True)
        s = self.s.query(Q("match", title="greyhounds"))
        r = s.execute()
        assert 1 == r.hits.total
