import json
from urllib.parse import urlencode

from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import signals
from django.conf import settings

from imageledger import models
from imageledger import signals as imageledger_signals
from imageledger.tests.utils import *

class TestAPIViews(TestImageledgerApp):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

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

    def test_list_autocomplete_lists_by_title(self):
        """The Lists autocomplete endpoint should allow lookup starting with a
        title and return all matches owned by that user"""
        title1 = 'test1'
        title2 = '1test'
        match = 'test'  # A startswith match
        lst1 = models.List.objects.create(title=title1, owner=self.user)
        lst2 = models.List.objects.create(title=title2, owner=self.user)
        self.req.force_login(self.user)
        resp = self.req.get('/api/v1/autocomplete/lists', {'title': match})
        assert 200 == resp.status_code
        self.assertEquals(1, len(resp.json()))

    def test_list_autocomplete(self):
        """The List autocomplete should only return Lists owned by the requesting user"""
        title = 'title'
        user2 = get_user_model().objects.create(username='other user')
        lst1 = models.List.objects.create(title=title, owner=user2)
        lst2 = models.List.objects.create(title=title, owner=self.user)
        lst3 = models.List.objects.create(title=title)
        self.req.force_login(self.user)
        resp = self.req.get('/api/v1/autocomplete/lists', {'title': title})
        assert 200 == resp.status_code
        self.assertEquals(1, len(resp.json()))

    def test_list_autocomplete_none_found(self):
        """The List autocomplete should return an empty list with a 200 response if no matching lists are found"""
        self.req.force_login(self.user)
        resp = self.req.get('/api/v1/autocomplete/lists', {'title': 'title'})
        assert 200 == resp.status_code
        self.assertEquals(0, len(resp.json()))

    def test_list_autocomplete_anon_user(self):
        """The List autocomplete should return a 403 on anonymous users"""
        resp = self.req.get('/api/v1/autocomplete/lists', {'title': 'title'})
        self.assertEqual(403, resp.status_code)

    def test_favorite_view_logged_in(self):
        """The Favorite view should require that a user be logged in"""
        img = models.Image.objects.create(url="example.com", license="CC0")
        resp = self.req.post('/api/v1/images/favorite/' + img.identifier)
        self.assertEqual(403, resp.status_code)

    def test_favorite_view_post(self):
        """The Favorite POST view should create a new Favorite object when a user requests it"""
        self.req.force_login(self.user)
        img = models.Image.objects.create(url="example.com", license="CC0")
        self.assertEqual(0, models.Favorite.objects.filter(user=self.user, image=img).count())
        resp = self.req.post('/api/v1/images/favorite/' + img.identifier)
        self.assertEqual(201, resp.status_code)
        self.assertEqual(1, models.Favorite.objects.filter(user=self.user, image=img).count())

    def test_favorite_view_put(self):
        """The Favorite PUT view should create a new Favorite object when a user
        requests it if it doesn't already exist"""
        self.req.force_login(self.user)
        img = models.Image.objects.create(url="example.com", license="CC0")
        self.assertEqual(0, models.Favorite.objects.filter(user=self.user, image=img).count())
        resp = self.req.put('/api/v1/images/favorite/' + img.identifier)
        self.assertEqual(201, resp.status_code)
        self.assertEqual(1, models.Favorite.objects.filter(user=self.user, image=img).count())

    def test_favorite_view_create_twice(self):
        """The Favorite view should be a no-op if a favorite is created twice via PUT"""
        self.req.force_login(self.user)
        img = models.Image.objects.create(url="example.com", license="CC0")
        self.assertEqual(0, models.Favorite.objects.filter(user=self.user, image=img).count())
        resp = self.req.put('/api/v1/images/favorite/' + img.identifier)
        self.assertEqual(201, resp.status_code)
        resp = self.req.put('/api/v1/images/favorite/' + img.identifier)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, models.Favorite.objects.filter(user=self.user, image=img).count())

    def test_favorite_view_delete(self):
        """The Favorite DELETE view should remove a favorite"""
        self.req.force_login(self.user)
        img = models.Image.objects.create(url="example.com", license="CC0")
        fave = models.Favorite.objects.create(image=img, user=self.user)
        self.assertEqual(1, models.Favorite.objects.filter(user=self.user, image=img).count())
        resp = self.req.delete('/api/v1/images/favorite/' + img.identifier)
        self.assertEqual(204, resp.status_code)
        self.assertEqual(0, models.Favorite.objects.filter(user=self.user, image=img).count())

    def test_favorite_view_delete_not_found(self):
        '''The Favorite delete view should return a 404 if the image doesn't exist'''
        self.req.force_login(self.user)
        resp = self.req.delete('/api/v1/images/favorite/fake')
        self.assertEqual(404, resp.status_code)

    def test_favorite_view_get(self):
        '''The Favorite get view should return 200 if the favorite exists'''
        self.req.force_login(self.user)
        img = models.Image.objects.create(url="example.com", license="CC0")
        fave = models.Favorite.objects.create(image=img, user=self.user)
        resp = self.req.get('/api/v1/images/favorite/' + img.identifier)
        self.assertEqual(200, resp.status_code)

    def test_favorite_view_get(self):
        '''The Favorite get view should return 204 if the favorite does not exist because Chrome'''
        self.req.force_login(self.user)
        resp = self.req.get('/api/v1/images/favorite/fake')
        self.assertEqual(204, resp.status_code)

    def test_favorite_list(self):
        """The logged-in user should be able to see a list of their Favorites"""
        self.req.force_login(self.user)
        img = models.Image.objects.create(url="example.com", license="CC0")
        fave = models.Favorite.objects.create(image=img, user=self.user)
        resp = self.req.get('/api/v1/images/favorites')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(resp.json()))

    def test_favorite_list_only_own(self):
        """The logged-in user should only see their own favorites"""
        img = models.Image.objects.create(url="example.com", license="CC0")
        fave = models.Favorite.objects.create(image=img, user=self.user)
        user2 = get_user_model().objects.create_user('user2', password='user2')
        self.req.force_login(user2)
        resp = self.req.get('/api/v1/images/favorites')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(0, len(resp.json()))

    def test_favorite_list_logged_in_only(self):
        """The favorites endpoint should not be displayed to unauthenticated users"""
        img = models.Image.objects.create(url="example.com", license="CC0")
        fave = models.Favorite.objects.create(image=img, user=self.user)
        resp = self.req.get('/api/v1/images/favorites')
        self.assertEqual(403, resp.status_code)

    # User tags
    def test_user_tags_post(self):
        """The User Tags POST view should create a new UserTag object for an existing tag"""
        self.req.force_login(self.user)
        img = models.Image.objects.create(url="example.com", license="CC0")
        tag = models.Tag.objects.create(name='tag')
        self.assertEqual(0, models.UserTags.objects.filter(user=self.user, image=img, tag=tag).count())
        resp = self.req.post('/api/v1/images/tags', {'identifier':  img.identifier,
                                                     'tag': tag.name})
        self.assertEqual(201, resp.status_code)
        self.assertEqual(1, models.UserTags.objects.filter(user=self.user, image=img, tag=tag).count())

    def test_user_tags_post_new_tag(self):
        """The User Tags POST view should create a new UserTag object for a new tag"""
        self.req.force_login(self.user)
        tagname = 'newtag'
        img = models.Image.objects.create(url="example.com", license="CC0")
        self.assertEqual(0, models.UserTags.objects.filter(user=self.user, image=img, tag__name=tagname).count())
        resp = self.req.post('/api/v1/images/tags', {'identifier':  img.identifier,
                                                     'tag': tagname})

        self.assertEqual(201, resp.status_code)
        self.assertEqual(1, models.Tag.objects.filter(name=tagname, source='user').count())
        self.assertEqual(1, models.UserTags.objects.filter(user=self.user, image=img, tag__name=tagname).count())

    def test_user_tags_delete(self):
        """The User Tags delete view should remove an existing UserTag object"""
        self.req.force_login(self.user)
        img = models.Image.objects.create(url="example.com", license="CC0")
        tag = models.Tag.objects.create(name='tag')
        user_tag = models.UserTags.objects.create(image=img, user=self.user, tag=tag)
        self.assertEqual(1, models.UserTags.objects.filter(user=self.user, image=img, tag=tag).count())
        resp = self.req.delete('/api/v1/images/tags/' + img.identifier + '/' + tag.name)
        self.assertEqual(204, resp.status_code)
        self.assertEqual(0, models.UserTags.objects.filter(user=self.user, image=img, tag=tag).count())

    def test_get_user_tags_for_image(self):
        """The User Tags list endpoint returns a list of tags for an image by the requesting user"""
        self.req.force_login(self.user)
        img = models.Image.objects.create(url="example.com", license="CC0")
        tag = models.Tag.objects.create(name='tag')
        user_tag = models.UserTags.objects.create(image=img, user=self.user, tag=tag)
        resp = self.req.get('/api/v1/images/tags/' + img.identifier)
        self.assertEqual(200, resp.status_code)
        jresp = resp.json()
        self.assertEqual(1, len(jresp))
        self.assertEqual('tag', jresp[0]['tag']['name'])

    def test_get_user_tags_for_image_only(self):
        """The User Tags list endpoint returns a list of tags for an image only by the requesting user"""
        self.req.force_login(self.user)
        img = models.Image.objects.create(url="example.com", license="CC0")
        tag = models.Tag.objects.create(name='tag')
        user2 = get_user_model().objects.create(username='other user')
        user_tag = models.UserTags.objects.create(image=img, user=user2, tag=tag)
        resp = self.req.get('/api/v1/images/tags/' + img.identifier)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(0, len(resp.json()))

    def test_user_tags_autocomplete_list(self):
        """The user tags autocomplete endpoint returns a list of tags created by that user"""
        self.req.force_login(self.user)
        img = models.Image.objects.create(url="example.com", license="CC0")
        tag = models.Tag.objects.create(name='tag1')
        user_tag = models.UserTags.objects.create(image=img, user=self.user, tag=tag)
        tag2 = models.Tag.objects.create(name='tag2')
        user_tag2 = models.UserTags.objects.create(image=img, user=self.user, tag=tag2)
        resp = self.req.get('/api/v1/autocomplete/tags')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(2, len(resp.json()))

    def test_user_tags_autocomplete_list_user_only(self):
        """The user tags autocomplete endpoint only returns a list of tags created by that user"""
        self.req.force_login(self.user)
        img = models.Image.objects.create(url="example.com", license="CC0")
        tag = models.Tag.objects.create(name='tag1', source='user')
        models.UserTags.objects.create(image=img, user=self.user, tag=tag)

        user2 = get_user_model().objects.create(username='other user')
        tag2 = models.Tag.objects.create(name='tag2', source='user')
        models.UserTags.objects.create(image=img, user=user2, tag=tag2)

        resp = self.req.get('/api/v1/autocomplete/tags')
        self.assertEqual(1, len(resp.json()))

    def test_user_tags_autocomplete_filter_by_tagname(self):
        """The user tags autocomplete endpoint only returns a list of matching tag names"""
        self.req.force_login(self.user)
        img = models.Image.objects.create(url="example.com", license="CC0")
        tag = models.Tag.objects.create(name='first', source='user')
        models.UserTags.objects.create(image=img, user=self.user, tag=tag)
        tag2 = models.Tag.objects.create(name='second', source='user')
        models.UserTags.objects.create(image=img, user=self.user, tag=tag2)

        resp = self.req.get('/api/v1/autocomplete/tags')
        self.assertEqual(2, len(resp.json()))

        resp = self.req.get('/api/v1/autocomplete/tags', {'name': 'first'})
        self.assertEqual(1, len(resp.json()))
        self.assertEqual('first', resp.json()[0]['tag']['name'])

        resp = self.req.get('/api/v1/autocomplete/tags', {'name': 'zero'})
        self.assertEqual(0, len(resp.json()))

    def test_remove_trailing_whitespace_from_tags(self):
        """[#110] Trailing whitespace should not be included in tags"""
        self.req.force_login(self.user)
        tagname = 'newtag'
        img = models.Image.objects.create(url="example.com", license="CC0")
        self.assertEqual(0, models.UserTags.objects.filter(user=self.user, image=img, tag__name=tagname).count())
        resp = self.req.post('/api/v1/images/tags', {'identifier':  img.identifier,
                                                     'tag': " " + tagname + " "})

        self.assertEqual(201, resp.status_code)
        self.assertEqual(1, models.Tag.objects.filter(name=tagname, source='user').count())
        self.assertEqual(1, models.UserTags.objects.filter(user=self.user, image=img, tag__name=tagname).count())
