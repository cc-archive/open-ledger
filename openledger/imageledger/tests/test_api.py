import json
from urllib.parse import urlencode

from rest_framework.test import APIClient
from django.urls import reverse
import jinja2

from imageledger import models, api
from imageledger.tests.utils import *

class TestAPIViews(TestImageledgerApp):

    def setUp(self):
        self.req = APIClient()

    def test_list_not_found(self):
        """The List endpoint should return a 404 if a slug is not found"""
        resp = self.req.get('/api/v1/lists/notfound')
        assert 404 == resp.status_code

    def test_list(self):
        """The List endpoint should return a 200 response if a List matches by slug"""
        lst = models.List.objects.create(title='test title')
        resp = self.req.get('/api/v1/lists/' + lst.slug)
        self.assertEquals(200, resp.status_code)

    def test_list_fields(self):
        """The List endpoint should return a JSON rendition of a list by slug"""
        title = 'test title'
        description = 'My test list ☃'
        creator_displayname = 'Jamal Doe'
        lst = models.List.objects.create(title=title, description=description, creator_displayname=creator_displayname)
        slug = lst.slug
        resp = self.req.get('/api/v1/lists/' + slug)
        assert 200 == resp.status_code
        obj = resp.json()
        assert title == obj['title']
        assert description == obj['description']
        assert creator_displayname == obj['creator_displayname']

    def test_list_image_data(self):
        """The List endpoint should return a JSON rendition of all a List's Images in reverse chronological order"""
        lst = models.List.objects.create(title='test')

        # Commit these in order so we're guaranteed which one is earlier
        img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')
        img2 = models.Image.objects.create(title='image title', url='http://example.com/2', license='CC0')

        lst.images.add(img1)
        lst.images.add(img2)
        lst.save()

        resp = self.req.get('/api/v1/lists/' + lst.slug)
        images = resp.json()['images']
        assert 2 == len(images)

        # Should be in reverse chronological order
        assert img1.id == images[1]['image']
        assert img2.id == images[0]['image']

    def test_list_delete_nonexistent_image(self):
        """The List endpoint should return a 404 if an unknown List is requested to be deleted"""
        resp = self.req.delete('/api/v1/lists/' + 'unknown')
        assert 404 == resp.status_code

    def test_list_delete(self):
        """The List endpoint should allow deleting Lists if a matching slug is found"""
        title = 'test'
        lst = models.List.objects.create(title=title)

        assert 1 == models.List.objects.filter(title=title).count()
        resp = self.req.delete('/api/v1/lists/' + lst.slug)
        self.assertEquals(204, resp.status_code)
        assert 0 == models.List.objects.filter(title=title).count()

    def test_lists_create_no_title(self):
        """The Lists endpoint should return a 422 Unprocessable Entity if the user tries to
        create a List with no title"""
        resp = self.req.post('/api/v1/lists', {'title': ""})
        self.assertEquals(400, resp.status_code)

    def test_lists_create_list(self):
        """The Lists endpoint should create a List if the user sends a POST request with at least a List title"""
        title = 'my list title'
        assert 0 == models.List.objects.filter(title=title).count()
        resp = self.req.post('/api/v1/lists', {'title': title})
        assert 201 == resp.status_code
        assert 1 == models.List.objects.filter(title=title).count()

    def test_lists_modify_list(self):
        """The Lists endpoint should modify a List if the user sends a PUT request"""
        title = 'my list title'
        lst = models.List.objects.create(title=title)
        img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')
        img2 = models.Image.objects.create(title='image title', url='http://example.com/2', license='CC0')

        assert 1 == models.List.objects.filter(title=title).count()
        assert 0 == models.List.objects.filter(title=title).first().images.count()

        resp = self.req.put('/api/v1/lists/' + lst.slug, {'images': [{'identifier': img1.identifier},
                                                                    {'identifier': img2.identifier}]})
        self.assertEquals(200, resp.status_code)
        self.assertEquals(2, models.List.objects.get(title=title).images.count())

        # Now "delete" one image
        resp = self.req.put('/api/v1/lists/' + lst.slug, {'images': [{'identifier': img1.identifier}]})
        assert 200 == resp.status_code
        self.assertEquals(1, models.List.objects.filter(title=title).first().images.count())

    def test_lists_create_while_modifying(self):
        """The modify-List endpoint should create a list if it doesn't already exist and return a 201"""
        title = 'my list title'
        resp = self.req.put('/api/v1/lists', {'title': title, 'image': []})
        assert 201 == resp.status_code
        assert 1 == models.List.objects.filter(title=title).count()

    def test_lists_create_list_with_images(self):
        """The Lists endpoint should create a List with all of the image identifier added"""
        title = 'my list title'
        img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')
        img2 = models.Image.objects.create(title='image title', url='http://example.com/2', license='CC0')

        resp = self.req.post('/api/v1/lists', data={'title': title, 'image': [img1.id, img2.id]})
        assert 201 == resp.status_code
        assert 2 == models.List.objects.filter(title=title).first().images.count()

    def test_add_to_list(self):
        """The Lists/Image endpoint should allow adding an Image to a List without modifying existing images"""
        lst = models.List.objects.create(title='test')
        img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')
        img2 = models.Image.objects.create(title='image title', url='http://example.com/2', license='CC0')
        lst.images.add(img1)
        lst.save()

        assert 1 == models.List.objects.filter(title='test').first().images.count()
        resp = self.req.post('/api/v1/lists/images', {'slug': lst.slug, 'image': img2.id})

        self.assertEquals(201, resp.status_code)
        assert 2 == models.List.objects.filter(title='test').first().images.count()

    def test_add_to_list_twice(self):
        """The Lists/Image endpoint should gracefully ignore attempts to add the same image twice and return a 200"""
        lst = models.List.objects.create(title='test')
        img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')
        assert 0 == models.List.objects.filter(title='test').first().images.count()

        resp = self.req.post('/api/v1/lists/images', {'slug': lst.slug, 'image': img1.id})
        assert 1 == models.List.objects.filter(title='test').first().images.count()
        assert 201 == resp.status_code

        resp = self.req.post('/api/v1/lists/images', {'slug': lst.slug, 'image': img1.id})
        assert 1 == models.List.objects.filter(title='test').first().images.count()

    def test_add_to_list_no_image(self):
        """The List/Image endpoint should return 404 if the user tries to add a nonexistent image"""
        lst = models.List.objects.create(title='test')
        resp = self.req.post('/api/v1/lists/images', {'slug': lst.slug, 'image': 'unknown'})
        assert 404 == resp.status_code

    def test_add_to_list_no_list(self):
        """The List/Image endpoint should return 404 if the user tries to add a nonexistent list"""
        lst = models.List.objects.create(title='test')
        img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')

        resp = self.req.post('/api/v1/lists/images', {'slug': 'made up', 'image': img1.id})
        assert 404 == resp.status_code

    def test_get_lists_by_title(self):
        """The Lists endpoint should allow lookup of lists by title"""
        title1 = 'test'
        title2 = 'yep'
        lst1 = models.List.objects.create(title=title1)
        lst2 = models.List.objects.create(title=title2)
        img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')
        img2 = models.Image.objects.create(identifier=img2.id, title='image title', url='http://example.com/2', license='CC0')
        lst2.images = [img1, img2]
        lst1.save()
        lst2.save()
        img1.save()
        img2.save()

        resp = self.req.get('/api/v1/lists?title=' + title1)
        assert 200 == resp.status_code
        assert 'lists' in resp.json()
        assert title1 == resp.json()['lists'][0]['title']
        assert lst1.slug == resp.json()['lists'][0]['slug']
        assert 0 == len(resp.json()['lists'][0]['images'])

        resp = self.req.get('/api/v1/lists?title='  + title2)
        assert 200 == resp.status_code
        assert 'lists' in resp.json()
        assert title2 == resp.json()['lists'][0]['title']
        assert lst2.slug == resp.json()['lists'][0]['slug']
        assert 2 == len(resp.json()['lists'][0]['images'])

    def test_get_lists_by_title(self):
        """The Lists endpoint should return an empty list if no matching lists are found"""
        resp = self.req.get('/api/v1/lists?title=not+found')
        assert 200 == resp.status_code  # Because Chrome; should be 404
        assert 'lists' in resp.json()
        assert 0 == len(resp.json()['lists'])

    def test_get_all_lists_by_title(self):
        """The Lists endpoint should allow lookup starting with a title and return all matches"""
        title1 = 'test1'
        title2 = '1test'
        match = 'test'  # A startswith match
        lst1 = models.List.objects.create(title=title1)
        lst2 = models.List.objects.create(title=title2)

        resp = self.req.get('/api/v1/lists?title='  + match)
        assert 200 == resp.status_code
        assert 'lists' in resp.json()
        assert 1 == len(resp.json()['lists'])

    def test_delete_from_list(self):
        """The Lists/Image endpoint should allow removing an Image from a List without modifying other images"""
        lst = models.List.objects.create(title='test')
        img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')
        img2 = models.Image.objects.create(title='image title', url='http://example.com/2', license='CC0')
        lst.images.add(img1)
        lst.images.add(img2)
        lst.save()

        assert 2 == models.List.objects.filter(title='test').first().images.count()
        resp = self.req.delete('/api/v1/lists/images', {'slug': lst.slug, 'image': img2.id})

#        resp = self.req.post('/api/v1/lists/images', {'slug': lst.slug, 'image': img2.id})
        self.assertEquals(204, resp.status_code)
        assert 1 == models.List.objects.filter(title='test').first().images.count()

    def test_delete_from_list_no_list(self):
        """The Lists/Image endpoint should 404 if a List does not exist"""
        img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')
        img1.save()
        resp = self.req.delete('/api/v1/lists/images', {'slug': 'unknown', 'image': img1.id})
        assert 404 == resp.status_code

    def test_delete_from_list_no_image(self):
        """The Lists/Image endpoint should 404 if the image requested to be removed does not exist"""
        lst = models.List.objects.create(title='test')
        resp = self.req.delete('/api/v1/lists/images', {'slug': lst.slug, 'image': 'unknown'})
        assert 404 == resp.status_code

# class TestAPIOwnedList(TestImageledgerApp):
#
#     def setUp(self):
#         super().setUp()
#         self.lst = models.List(title='test')
#         self.img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')
#         self.img2 = models.Image.objects.create(title='image title', url='http://example.com/2', license='CC0')
#         self.user = models.User(ccid='user1', email='user@example.com')
#         self.lst.creator = self.user
#         self.lst.images = [self.img1, self.img2]
#         self.lst.save()
#         self.img1.save()
#         self.img2.save()
#
#
#     def test_list_operation_owner_only(self):
#         """The Lists endpoint should only allow modification of an owned list by the owner"""
#         pass
#
#     def test_create_owned_list(self):
#         """The API should allow creation of a list owned by the logged-in user id"""
#         title = 'my list title'
#         assert 0 == models.List.objects.filter(title=title).count()
#         resp = self.req.post('/api/v1/lists', {'title': title})
#         lst = models.List.objects.filter(title=title).one()
#         pass  # Not yet working
#

class TestAPI(TestImageledgerApp):
    """Methods that test the API calls directly"""

    def test_get_all_lists_startswith_title(self):
        """The get_lists function should allow lookup of lists starting with title and return all matches"""
        title1 = 'test1'
        title2 = '1test'
        match = 'test'  # A startswith match
        lst1 = models.List.objects.create(title=title1)
        lst2 = models.List.objects.create(title=title2)
        lst1.save()
        lst2.save()

        assert 1 == api.get_lists(title='test', match_method='startswith').count()
        assert 2 == api.get_lists(title='test', match_method='contains').count()
