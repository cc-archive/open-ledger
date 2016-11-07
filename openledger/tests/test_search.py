import os
import time

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.connections import connections
from flask import request, url_for
import pytest
from testing.elasticsearch import ElasticSearchServer

from openledger import app as ol
from openledger import search
from openledger.tests.utils import *

# Monkeypatch support for ES 5
@property
def arguments(self):
    if 'node.local' in self.config:
        self.config['node.attr.local'] = self.config['node.local']
        del self.config['node.local']
    if 'discovery.zen.ping.multicast.enabled' in self.config:
        del self.config['discovery.zen.ping.multicast.enabled']

    args = [
        '-E{0}={1}'.format(key, value)
        for key, value in self.config.items()
    ]
    if not self._foreground:
        args.append('-d')
    return args

ElasticSearchServer.arguments = arguments  # monkeypatch removed config

def mock_es():
    with ElasticSearchServer() as test_es:
        es = Elasticsearch(host=test_es._bind_host,
                           port=test_es._bind_port)
        return es

@pytest.fixture(scope='class')
def elasticsearch(request):
    test_es = ElasticSearchServer()
    test_es.start()
    request.addfinalizer(test_es.stop)
    request.cls.test_es = test_es

@pytest.mark.usefixtures("elasticsearch")
class TestSearch(TestOpenLedgerApp):

    def setUp(self):
        super().setUp()
        es = Elasticsearch(host=self.test_es._bind_host,
                           port=self.test_es._bind_port)
        connections.add_connection('default', es)
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
        """It should be possible to retrieve a database item by auto-id"""
        search.Image.init()
        image = search.db_image_to_index(self.img1)
        image.save()
        s = self.s.query(Q("match", title="greyhounds"))
        r = s.execute()
        assert 1 == r.hits.total
