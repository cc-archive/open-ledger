import os
import unittest

from openledger import app
from openledger.tests.utils import *

import openledger.models as models

class TestModels(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config.from_pyfile(TESTING_CONFIG)
        with app.app_context():
            models.db.create_all()

    def tearDown(self):
        with app.app_context():
            models.db.session.close()
            models.db.drop_all()

    def test_db_connection(self):
        """The test database should be accessible"""
        assert models.Image.query.count() == 0

    def test_image_model(self):
        """It should be possible to create an Image record with a few basic fields"""
        assert models.Image.query.count() == 0
        image = models.Image()
        image.url = 'http://example.com'
        image.license = 'CC0'
        models.db.session.add(image)
        models.db.session.commit()
        assert models.Image.query.count() == 1

    def test_image_model_repr(self):
        """An image model representation should include its identifer, url, and creator"""
        url = "http://example.com"
        creator = "jane doe"
        image = models.Image(url=url, license="CC0", creator=creator)
        assert url in image.__repr__()
        assert creator in image.__repr__()


    def test_image_model_identifier(self):
        """The identifier-creation function should return the same value for each iteration"""
        url = 'http://example.com'
        last_identifier = None
        for i in range(0, 100):
            identifier = models.create_identifier(url)
            if last_identifier:
                assert last_identifier == identifier
            else:
                last_identifier = identifier

    def test_tag_model(self):
        """It should be possible to create a Tag with a few basic fields"""
        assert models.Tag.query.count() == 0
        tag = models.Tag()
        tag.name = 'myname'
        tag.foreign_identifier = '1234'
        models.db.session.add(tag)
        models.db.session.commit()
        assert models.Tag.query.count() == 1

    def test_tag_image(self):
        """It should be possible to associate a tag with an image"""
        image = models.Image(url='http://example.com', license="CC0")
        tag = models.Tag(name='tagname', foreign_identifier='tagid')
        models.db.session.add(tag)
        models.db.session.add(image)
        models.db.session.commit()
        image_obj = models.Image.query.first()
        assert image_obj.tags.count() == 0
        image_obj.tags.append(tag)
        models.db.session.commit()
        assert image_obj.tags.count() == 1

    def test_tags_list_image(self):
        """The `tags_list` field on the `Image` table should contain an array of values"""
        image = models.Image(url='http://example.com', license="CC0")
        tags_list = ['a', 'b']
        image.tags_list = tags_list
        models.db.session.add(image)
        models.db.session.commit()

        # Get it back out and assert that it's a list again
        image = models.Image.query.first()
        assert 2 == len(image.tags_list)
        assert "a" == image.tags_list[0]

    def test_list(self):
        """It should be possible to create an empty List"""
        assert 0 == models.List.query.count()
        lst = models.List(title='test')
        models.db.session.add(lst)
        models.db.session.commit()

        assert 1 == models.List.query.count()

    def test_list(self):
        """It should be possible to create a List and add an image to it"""

        image = models.Image(url='http://example.com', license="CC0")
        lst = models.List(title='test', images=[image])
        models.db.session.add(lst)
        models.db.session.add(image)
        models.db.session.commit()

        assert 1 == models.List.query.count()
        assert 1 == models.List.query.first().images.count()
        assert image == models.List.query.first().images.first()

    def test_slugify(self):
        """It should be possible to generate a URL-safe identifier out of an arbitrary list of keywords"""
        # A string, some crazy unicode, an integer
        items = ['my list', '☃', 1]
        assert 'my-list--1' == models.create_slug(items)

    def test_slugify_list(self):
        """When a List is created, a slug should be automatically generated"""
        title = 'my list about unicode snowmen ☃'
        lst = models.List(title=title)
        models.db.session.add(lst)
        models.db.session.commit()

        lst = models.List.query.first()
        assert lst.slug.startswith('my-list-about-unicode-snowmen-')

    def test_slugify_unique(self):
        """Creating two lists with the same title should not result in a duplicate slug"""
        title = "Duplicate title"
        expected_slugged_title = "duplicate-title"
        lst1 = models.List(title=title)
        lst2 = models.List(title=title)
        models.db.session.add(lst1)
        models.db.session.add(lst2)
        models.db.session.commit()

        lst1 = models.List.query[0]
        lst2 = models.List.query[1]
        # They should start the same, but not be identical
        assert lst1.slug.startswith(expected_slugged_title)
        assert lst2.slug.startswith(expected_slugged_title)
        assert lst1.slug != lst2.slug
