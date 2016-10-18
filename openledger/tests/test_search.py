import os
import unittest

import jinja2
from flask_testing import TestCase

from openledger import app as ol
from openledger.tests.utils import *
import openledger.models as models

TESTING_CONFIG = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'settings.py')

# Tests of our search interface (not of the provider pass-throughs)
class TestSearch(TestCase):

    def create_app(self):
        app = ol
        app.config.from_pyfile(TESTING_CONFIG)
        app.jinja_env.undefined = jinja2.StrictUndefined
        return app

    def setUp(self):
        models.db.create_all()

    def tearDown(self):
        models.db.session.close()
        models.db.session.remove()
        models.db.drop_all()

    def test_search_interface(self):
        """The search engine should return results from the loaded database"""
        rv = self.client.get('/source/openimages')
        assert rv.status_code == 200

    def test_search_database(self):
        """The search database should start up empty"""
        assert 0 == models.Image.query.count()

    def test_search_interface_no_results(self):
        """The search engine should return a results page even if there are no results"""
        query = 'test'
        rv = self.client.get('/source/openimages', query_string={'search': query, 'search_fields': 'title'})
        assert rv.status_code == 200
        assert len(select_node(rv, '.t-image-result')) == 0

    def test_search_interface_some_results(self):
        """The search feature should return at least one matching result"""
        query = 'test'
        image = models.Image(url="http://example.com", title=query, license="CC0", identifier="1234")
        tag = models.Tag(name='tag', foreign_identifier='tag')
        image.tags.append(tag)
        models.db.session.add(image)
        models.db.session.commit()

        rv = self.client.get('/source/openimages', query_string={'search': query, 'search_fields': 'title'})
        assert rv.status_code == 200
        assert len(select_node(rv, '.t-image-result')) == 1

    def test_search_image_only(self):
        """The search feature should return a result where an image matches in title but has no tags"""
        query = 'test'
        image = models.Image(url="http://example.com", title=query, license="CC0", identifier="1234")
        models.db.session.add(image)
        models.db.session.commit()

        rv = self.client.get('/source/openimages', query_string={'search': query, 'search_fields': 'title'})
        assert rv.status_code == 200
        assert len(select_node(rv, '.t-image-result')) == 1
