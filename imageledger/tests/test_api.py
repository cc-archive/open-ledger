import json
from urllib.parse import urlencode

from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model

from imageledger import models
from imageledger.tests.utils import *

class TestAPIViews(TestImageledgerApp):

    def setUp(self):
        self.req = APIClient()
        self.username = 'testuser'
        self.user = get_user_model().objects.create_user(self.username, password=self.username)

    def test_list_not_found(self):
        """The List endpoint should return a 404 if a slug is not found"""
        resp = self.req.get('/api/v1/lists/notfound')
        assert 404 == resp.status_code

    def test_list_not_public(self):
        """The List endpoint should return a 403 response if a List matches by slug but is not public"""
        lst = models.List.objects.create(title='test title')
        resp = self.req.get('/api/v1/lists/' + lst.slug)
        self.assertEquals(403, resp.status_code)

    def test_list_public(self):
        """The List endpoint should return a 200 response if a List matches by slug and is public"""
        lst = models.List.objects.create(title='test title', is_public=True)
        resp = self.req.get('/api/v1/lists/' + lst.slug)
        self.assertEquals(200, resp.status_code)

    def test_list_multiple(self):
        """The List endpoint should only return one list per slug"""
        title1 = 'test'
        title2 = 'test 2'
        lst1 = models.List.objects.create(title=title1, is_public=True)
        lst2 = models.List.objects.create(title=title2, is_public=True)
        resp = self.req.get('/api/v1/lists/' + lst1.slug)
        self.assertEquals(200, resp.status_code)
        self.assertEqual(title1, resp.json()['title'])

        resp = self.req.get('/api/v1/lists/' + lst2.slug)
        self.assertEquals(200, resp.status_code)
        self.assertEqual(title2, resp.json()['title'])

    def test_list_not_public_owner(self):
        """The List endpoint should return a 200 response if a List matches by slug and
        and is owned by the requestor, even if it not public"""
        lst = models.List.objects.create(title='test title', owner=self.user)
        self.req.force_login(self.user)
        resp = self.req.get('/api/v1/lists/' + lst.slug)
        self.assertEquals(200, resp.status_code)

        # But not if they log out
        self.req.logout()
        resp = self.req.get('/api/v1/lists/' + lst.slug)
        self.assertEquals(403, resp.status_code)


    def test_list_fields(self):
        """The List endpoint should return a JSON rendition of a list by slug"""
        title = 'test title'
        description = 'My test list ☃'
        creator_displayname = 'Jamal Doe'
        lst = models.List.objects.create(title=title, description=description, creator_displayname=creator_displayname, is_public=True)
        slug = lst.slug
        resp = self.req.get('/api/v1/lists/' + slug)
        assert 200 == resp.status_code
        obj = resp.json()
        assert title == obj['title']
        assert description == obj['description']
        assert creator_displayname == obj['creator_displayname']

    def test_list_image_data(self):
        """The List endpoint should return a JSON rendition of all a List's Images in reverse chronological order"""
        lst = models.List.objects.create(title='test', is_public=True)

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
        assert img1.identifier == images[1]['identifier']
        assert img2.identifier == images[0]['identifier']

    def test_list_delete_nonexistent_image(self):
        """The List endpoint should return a 404 if an unknown List is requested to be deleted"""
        resp = self.req.delete('/api/v1/lists/' + 'unknown')
        assert 404 == resp.status_code

    def test_list_delete(self):
        """The List endpoint should allow deleting Lists if a matching slug is found"""
        title = 'test'
        lst = models.List.objects.create(title=title, owner=self.user)
        self.req.force_login(self.user)

        assert 1 == models.List.objects.filter(title=title).count()
        resp = self.req.delete('/api/v1/lists/' + lst.slug)
        self.assertEquals(204, resp.status_code)
        assert 0 == models.List.objects.filter(title=title).count()

    def test_list_delete_not_owner(self):
        """The List endpoint should not allow deleting Lists if the requestor is not the owner"""
        title = 'test'
        lst = models.List.objects.create(title=title, owner=self.user)
        resp = self.req.delete('/api/v1/lists/' + lst.slug)
        self.assertEquals(403, resp.status_code)

    def test_lists_create_no_title(self):
        """The Lists endpoint should return a 400 Unprocessable Entity if the user tries to
        create a List with no title"""
        self.req.force_login(self.user)
        resp = self.req.post('/api/v1/lists', {'title': ""})
        self.assertEquals(400, resp.status_code)

    def test_lists_create_list(self):
        """The Lists endpoint should create a List if the logged-in user sends a POST request with at least a List title"""
        title = 'my list title'
        assert 0 == models.List.objects.filter(title=title).count()
        self.req.force_login(self.user)
        resp = self.req.post('/api/v1/lists', {'title': title})
        assert 201 == resp.status_code
        lst = models.List.objects.get(title=title)
        self.assertEquals(self.user, lst.owner)

    def test_lists_create_list_auth_required(self):
        """The Lists endpoint should not allow List creation if the user isn't logged in"""
        title = 'my list title'
        assert 0 == models.List.objects.filter(title=title).count()
        resp = self.req.post('/api/v1/lists', {'title': title})
        self.assertEquals(403, resp.status_code)

    def test_lists_modify_list(self):
        """The Lists endpoint should modify a List if the owner sends a PUT request with replace=true """
        title = 'my list title'
        lst = models.List.objects.create(title=title, owner=self.user)
        self.req.force_login(self.user)
        img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')
        img2 = models.Image.objects.create(title='image title', url='http://example.com/2', license='CC0')

        assert 1 == models.List.objects.filter(title=title).count()
        assert 0 == models.List.objects.filter(title=title).first().images.count()

        resp = self.req.put('/api/v1/lists/' + lst.slug, {'images': [{'identifier': img1.identifier},
                                                                     {'identifier': img2.identifier}]})
        self.assertEquals(200, resp.status_code)
        self.assertEquals(2, models.List.objects.get(title=title).images.count())

        # Now "delete" one image with replace=True
        resp = self.req.put('/api/v1/lists/' + lst.slug, {'replace': True,
                                                          'images': [{'identifier': img1.identifier}]})
        assert 200 == resp.status_code
        self.assertEquals(1, models.List.objects.filter(title=title).first().images.count())

    def test_add_to_list(self):
        """The Lists endpoint should allow adding an Image to a List without modifying existing images"""
        lst = models.List.objects.create(title='test', owner=self.user)
        self.req.force_login(self.user)
        img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')
        img2 = models.Image.objects.create(title='image title', url='http://example.com/2', license='CC0')
        lst.images.add(img1)
        lst.save()

        assert 1 == models.List.objects.filter(title='test').first().images.count()
        resp = self.req.put('/api/v1/lists/' + lst.slug, {'images': [{'identifier': img2.identifier}]})
        self.assertEquals(200, resp.status_code)
        assert 2 == models.List.objects.filter(title='test').first().images.count()

    def test_add_to_list_twice(self):
        """The Lists/Image endpoint should gracefully ignore attempts to add the same image twice and return a 200"""
        lst = models.List.objects.create(title='test', owner=self.user)
        self.req.force_login(self.user)
        img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')
        assert 0 == models.List.objects.filter(title='test').first().images.count()

        resp = self.req.put('/api/v1/lists/' + lst.slug, {'images': [{'identifier': img1.identifier}]})
        assert 1 == models.List.objects.filter(title='test').first().images.count()
        assert 200 == resp.status_code

        resp = self.req.put('/api/v1/lists/' + lst.slug, {'images': [{'identifier': img1.identifier}]})
        assert 1 == models.List.objects.filter(title='test').first().images.count()

    def test_add_to_list_no_image(self):
        """The List/Image endpoint should return 404 if the user tries to add a nonexistent image"""
        lst = models.List.objects.create(title='test', owner=self.user)
        self.req.force_login(self.user)
        resp = self.req.put('/api/v1/lists/' + lst.slug, {'images': [{'identifier': 'xxxx'}]})
        404 == resp.status_code

    def test_get_lists_by_title(self):
        """The Lists endpoint should allow lookup of lists by title"""
        title1 = 'test'
        title2 = 'yep'
        lst1 = models.List.objects.create(title=title1, is_public=True)
        lst2 = models.List.objects.create(title=title2, is_public=True)
        img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')
        img2 = models.Image.objects.create(identifier=img2.id, title='image title', url='http://example.com/2', license='CC0')
        lst2.images = [img1, img2]
        lst1.save()
        lst2.save()
        img1.save()
        img2.save()

        resp = self.req.get('/api/v1/lists?title=' + title1)
        assert 200 == resp.status_code
        assert title1 == resp.json()[0]['title']
        assert lst1.slug == resp.json()[0]['slug']
        assert 0 == len(resp.json()[0]['images'])

        resp = self.req.get('/api/v1/lists?title='  + title2)
        assert 200 == resp.status_code
        assert title2 == resp.json()[0]['title']
        assert lst2.slug == resp.json()[0]['slug']
        assert 2 == len(resp.json()[0]['images'])

    def test_get_lists_by_title(self):
        """The Lists endpoint should return an empty list if no matching lists are found"""
        resp = self.req.get('/api/v1/lists?title=not+found')
        assert 200 == resp.status_code  # Because Chrome; ideally would be 404
        assert 0 == len(resp.json())

    def test_get_all_lists_by_title(self):
        """The Lists endpoint should allow lookup starting with a title and return all matches"""
        title1 = 'test1'
        title2 = '1test'
        match = 'test'  # A startswith match
        lst1 = models.List.objects.create(title=title1, is_public=True)
        lst2 = models.List.objects.create(title=title2, is_public=True)

        resp = self.req.get('/api/v1/lists', {'title': match})
        assert 200 == resp.status_code
        assert 1 == len(resp.json())

    def test_delete_from_list(self):
        """The Lists/Image endpoint should allow removing an Image from a List without modifying other images"""
        lst = models.List.objects.create(title='test', owner=self.user)
        self.req.force_login(self.user)
        img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')
        img2 = models.Image.objects.create(title='image title', url='http://example.com/2', license='CC0')
        lst.images.add(img1)
        lst.images.add(img2)
        lst.save()

        assert 2 == models.List.objects.filter(title='test').first().images.count()

        resp = self.req.delete('/api/v1/lists/' + lst.slug,  {'images': [{'identifier': img2.identifier}]})

        self.assertEquals(204, resp.status_code)
        assert 1 == models.List.objects.filter(title='test').first().images.count()

    def test_delete_from_list_no_list(self):
        """The Lists/Image endpoint should 404 if a List does not exist"""
        self.req.force_login(self.user)
        resp = self.req.delete('/api/v1/lists/image/unknown')
        assert 404 == resp.status_code

    def test_delete_from_list_no_image(self):
        """The Lists/Image endpoint should 404 if the image requested to be removed does not exist"""
        lst = models.List.objects.create(title='test', owner=self.user)
        self.req.force_login(self.user)
        resp = self.req.delete('/api/v1/lists/' + lst.slug, {'images': [{'identifier': 'unknown'}]})
        assert 404 == resp.status_code
