import json

import responses
import jinja2
from flask_testing import TestCase
from flask import request, url_for

from openledger import app, models
from openledger.tests.utils import *

class TestAPIViews(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config.from_pyfile(TESTING_CONFIG)
        return app

    def setUp(self):
        with app.app_context():
            models.db.create_all()

    def tearDown(self):
        with app.app_context():
            models.db.session.close()
            models.db.session.remove()
            models.db.drop_all()

    def test_list_not_found(self):
        """The List endpoint should return a 404 if a slug is not found"""
        rv = self.client.get('/api/v1/list/not-found')
        assert 404 == rv.status_code

    def test_list(self):
        """The List endpoint should return a 200 response if a List matches by slug"""
        lst = models.List(title='test title')
        models.db.session.add(lst)
        models.db.session.commit()
        slug = lst.slug
        rv = self.client.get('/api/v1/list/' + slug)
        assert 200 == rv.status_code

    def test_list_fields(self):
        """The List endpoint should return a JSON rendition of a list by slug"""
        title = 'test title'
        description = 'My test list ☃'
        creator_displayname = 'Jamal Doe'
        lst = models.List(title=title, description=description, creator_displayname=creator_displayname)
        models.db.session.add(lst)
        models.db.session.commit()
        slug = lst.slug
        rv = self.client.get('/api/v1/list/' + slug)
        assert 200 == rv.status_code
        obj = rv.json
        assert title == obj['title']
        assert description == obj['description']
        assert creator_displayname == obj['creator_displayname']

    def test_list_image_data(self):
        """The List endpoint should return a JSON rendition of all a List's Images in reverse chronological order"""
        lst = models.List(title='test')

        # Commit these in order so we're guaranteed which one is earlier
        img1 = models.Image(identifier='1', title='image title', url='http://example.com/1', license='CC0')
        models.db.session.add(img1)
        models.db.session.commit()

        img2 = models.Image(identifier='2', title='image title', url='http://example.com/2', license='CC0')
        models.db.session.add(img2)
        models.db.session.commit()

        lst.images.append(img1)
        lst.images.append(img2)
        models.db.session.add(lst)
        models.db.session.commit()

        slug = lst.slug
        rv = self.client.get('/api/v1/list/' + slug)
        images = rv.json['images']
        assert 2 == len(images)

        # Should be in reverse chronological order
        assert '1' == images[1]['identifier']
        assert '2' == images[0]['identifier']

    def test_list_delete_nonexistent_image(self):
        """The List endpoint should return a 404 if an unknown List is requested to be deleted"""
        rv = self.client.delete('/api/v1/lists', data={'slug': 'unknown'})
        assert 404 == rv.status_code

    def test_list_delete(self):
        """The List endpoint should allow deleting Lists if a matching slug is found"""
        title = 'test'
        lst = models.List(title=title)
        models.db.session.add(lst)
        models.db.session.commit()
        assert 1 == models.List.query.filter(models.List.title==title).count()
        rv = self.client.delete('/api/v1/lists', data={'slug': lst.slug})
        assert 204 == rv.status_code
        assert 0 == models.List.query.filter(models.List.title==title).count()

    def test_lists_create_no_title(self):
        """The Lists endpoint should return a 422 Unprocessable Entity if the user tries to
        create a List with no title"""
        rv = self.client.post('/api/v1/lists', data={'title': None})
        assert 422 == rv.status_code

    def test_lists_create_list(self):
        """The Lists endpoint should create a List if the user sends a POST request with at least a List title"""
        title = 'my list title'
        assert 0 == models.List.query.filter(models.List.title==title).count()
        rv = self.client.post('/api/v1/lists', data={'title': title})
        assert 201 == rv.status_code
        assert 1 == models.List.query.filter(models.List.title==title).count()

    def test_lists_modify_list(self):
        """The Lists endpoint should modify a List if the user sends a PUT request"""
        title = 'my list title'
        lst = models.List(title=title)
        img1 = models.Image(identifier='1', title='image title', url='http://example.com/1', license='CC0')
        img2 = models.Image(identifier='2', title='image title', url='http://example.com/2', license='CC0')
        models.db.session.add(lst)
        models.db.session.add(img1)
        models.db.session.add(img2)
        models.db.session.commit()
        assert 1 == models.List.query.filter(models.List.title==title).count()
        assert 0 == models.List.query.filter(models.List.title==title).first().images.count()
        rv = self.client.put('/api/v1/lists', data={'slug': lst.slug, 'identifiers': ['1', '2']})
        assert 200 == rv.status_code
        assert 2 == models.List.query.filter(models.List.title==title).first().images.count()

        # Now "delete" one image
        rv = self.client.put('/api/v1/lists', data={'slug': lst.slug, 'identifiers': ['2']})
        assert 200 == rv.status_code
        assert 1 == models.List.query.filter(models.List.title==title).first().images.count()

    def test_lists_create_while_modifying(self):
        """The modify-List endpoint should create a list if it doesn't already exist and return a 201"""
        title = 'my list title'
        rv = self.client.put('/api/v1/lists', data={'title': title, 'identifiers': []})
        assert 201 == rv.status_code
        assert 1 == models.List.query.filter(models.List.title==title).count()

    def test_lists_create_list_with_images(self):
        """The Lists endpoint should create a List with all of the image identifiers added"""
        title = 'my list title'
        img1 = models.Image(identifier='1', title='image title', url='http://example.com/1', license='CC0')
        img2 = models.Image(identifier='2', title='image title', url='http://example.com/2', license='CC0')
        models.db.session.add(img1)
        models.db.session.add(img2)
        models.db.session.commit()

        rv = self.client.post('/api/v1/lists', data={'title': title, 'identifiers': ['1', '2']})
        assert 201 == rv.status_code
        assert 2 == models.List.query.filter(models.List.title==title).first().images.count()

    def test_add_to_list(self):
        """The Lists/Image endpoint should allow adding an Image to a List without modifying existing images"""
        lst = models.List(title='test')
        img1 = models.Image(identifier='1', title='image title', url='http://example.com/1', license='CC0')
        img2 = models.Image(identifier='2', title='image title', url='http://example.com/2', license='CC0')
        lst.images = [img1]
        models.db.session.add(lst)
        models.db.session.add(img1)
        models.db.session.add(img2)
        models.db.session.commit()

        assert 1 == models.List.query.filter(models.List.title=='test').first().images.count()
        rv = self.client.post('/api/v1/list/images', data={'slug': lst.slug, 'identifier': '2'})

        assert 201 == rv.status_code
        assert 2 == models.List.query.filter(models.List.title=='test').first().images.count()

    def test_add_to_list_no_image(self):
        """The List/Image endpoint should return 404 if the user tries to add a nonexistent image"""
        lst = models.List(title='test')
        models.db.session.add(lst)
        models.db.session.commit()
        rv = self.client.post('/api/v1/list/images', data={'slug': lst.slug, 'identifier': '2'})
        assert 404 == rv.status_code

    def test_add_to_list_no_image(self):
        """The List/Image endpoint should return 404 if the user tries to add a nonexistent list"""
        lst = models.List(title='test')
        img1 = models.Image(identifier='1', title='image title', url='http://example.com/1', license='CC0')
        models.db.session.add(lst)
        models.db.session.add(img1)
        models.db.session.commit()
        rv = self.client.post('/api/v1/list/images', data={'slug': 'made up', 'identifier': '1'})
        assert 404 == rv.status_code
