import os
import unittest

from openledger import app
from openledger.tests.utils import *

import openledger.models as models

TESTING_CONFIG = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'settings.py')

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
        image.identifier='1234'
        models.db.session.add(image)
        models.db.session.commit()
        assert models.Image.query.count() == 1

    def test_image_model_repr(self):
        """An image model representation should include its identifer, url, and creator"""
        url = "http://example.com"
        creator = "jane doe"
        identifier = "1234"
        image = models.Image(url=url, license="CC0", identifier=identifier, creator=creator)
        assert url in image.__repr__()
        assert creator in image.__repr__()
        assert identifier in image.__repr__()

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
        image = models.Image(url='http://example.com', license="CC0", identifier="1234")
        tag = models.Tag(name='tagname', foreign_identifier='tagid')
        models.db.session.add(tag)
        models.db.session.add(image)
        models.db.session.commit()
        image_obj = models.Image.query.first()
        assert image_obj.tags.count() == 0
        image_obj.tags.append(tag)
        models.db.session.commit()
        assert image_obj.tags.count() == 1
