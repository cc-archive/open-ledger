import os
import unittest

import jinja2

from openledger import app
from openledger.tests.utils import *
import openledger.models as models

TESTING_CONFIG = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'settings.py')

# Tests of our search interface (not of the provider pass-throughs)
class TestSearch(unittest.TestCase):

    def setUp(self):
        app.config.from_pyfile(TESTING_CONFIG)
        self.app = app.test_client()
        app.jinja_env.undefined = jinja2.StrictUndefined
        with app.app_context():
            models.db.create_all()

    def tearDown(self):
        with app.app_context():
            models.db.session.close()
            models.db.drop_all()

    def test_search_interface(self):
        """The search engine should return results from the loaded database"""
        rv = self.app.get('/source/openimages')
        assert rv

    def test_search_interface_no_results(self):
        """The search engine should return a results page even if there are no results"""
        query = 'test'
        rv = self.app.get('/source/openimages', query_string={'search': query, 'search_fields': 'title'})
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

        rv = self.app.get('/source/openimages', query_string={'search': query, 'search_fields': 'title'})
        assert rv.status_code == 200
        assert len(select_node(rv, '.t-image-result')) == 1

    def test_search_image_only(self):
        """The search feature should return a result where an image matches in title but has no tags"""
        query = 'test'
        image = models.Image(url="http://example.com", title=query, license="CC0", identifier="1234")
        models.db.session.add(image)
        models.db.session.commit()

        rv = self.app.get('/source/openimages', query_string={'search': query, 'search_fields': 'title'})
        assert rv.status_code == 200
        assert len(select_node(rv, '.t-image-result')) == 1
