import os
import logging

from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model

from imageledger import models
from imageledger.tests.utils import *

class TestListViews(TestImageledgerApp):

    def setUp(self):
        super().setUp()
        self.lst = models.List.objects.create(title='test')
        self.img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')
        self.img2 = models.Image.objects.create(title='image title', url='http://example.com/2', license='CC0')
        self.lst.images.add(self.img1)
        self.lst.images.add(self.img2)
        self.username = 'testuser'
        self.user = get_user_model().objects.create_user(self.username, password=self.username)

    def _login_and_own(self):
        self.client.force_login(self.user)
        self.lst.owner = self.user
        self.lst.save()

    def test_view_my_list_detail(self):
        """It should be possible to view a list's information"""
        self._login_and_own()
        resp = self.client.get(reverse('my-list-update', kwargs={'slug': self.lst.slug}))
        assert 200 == resp.status_code
        p = select_node(resp, '.t-list-title')
        assert self.lst.title == p.text.strip()

    def test_view_my_list_not_found(self):
        """A request to view a list that doesn't exist should ultimately 404"""
        self._login_and_own()
        resp = self.client.get(reverse('my-list-update', kwargs={'slug': 'unknown'}), follow=True)
        assert 404 == resp.status_code

    def test_view_my_list_images(self):
        """A request to view a list should show its available images"""
        self._login_and_own()
        resp = self.client.get(reverse('my-list-update', kwargs={'slug': self.lst.slug}))
        p = select_nodes(resp, '.t-image-result')
        assert 2 == len(p)

    def test_update_my_list(self):
        """A request to update a list via a POST request should update the list values"""
        desc = 'new desc'
        title = 'new title'
        self._login_and_own()
        resp = self.client.post(reverse('my-list-update', kwargs={'slug': self.lst.slug}), {'description': desc,
                'title': title})
        lst = models.List.objects.get(slug=self.lst.slug)
        assert desc == lst.description
        assert title == lst.title

    def test_update_my_list_redirect(self):
        """A request to update a list via a POST request should redirect to the list detail when done"""
        self._login_and_own()
        resp = self.client.post(reverse('my-list-update', kwargs={'slug': self.lst.slug}),
                                {'description': self.lst.description,
                                'title': self.lst.title})
        self.assertRedirects(resp, reverse('my-list-update', kwargs={'slug': self.lst.slug}))

    def test_my_lists(self):
        """The my-lists page should load for a logged-in user"""
        self.client.force_login(self.user)
        resp = self.client.get(reverse('my-lists'))
        self.assertEquals(200, resp.status_code)

    def test_list_delete_owner_only(self):
        """Only an owner should be able to delete a List"""
        assert self.lst.owner != self.user
        assert models.List.objects.filter(slug=self.lst.slug).exists()
        resp = self.client.post(reverse('my-list-delete', kwargs={'slug': self.lst.slug}), follow=True)
        self.assertEquals(404, resp.status_code)
        # Should still exist
        assert models.List.objects.filter(slug=self.lst.slug).exists()

    def test_list_delete_owner(self):
        """An owner should be able to delete a List"""
        self._login_and_own()
        resp = self.client.post(reverse('my-list-delete', kwargs={'slug': self.lst.slug}))
        self.assertRedirects(resp, reverse('my-lists'))
        assert not models.List.objects.filter(slug=self.lst.slug).exists()

    def test_public_list(self):
        """The public list detail page should return a List if it is public"""
        self.lst.is_public = True
        self.lst.save()

        resp = self.client.get(reverse('list-detail', kwargs={'slug': self.lst.slug}))
        self.assertEquals(200, resp.status_code)
        p = select_node(resp, ".t-list-title")
        self.assertEquals(self.lst.title, p.text.strip())

    def test_public_list_must_be_public(self):
        """The public list detail page should return a 404 if the list is not public"""
        self.lst.is_public = False
        self.lst.save()

        resp = self.client.get(reverse('list-detail', kwargs={'slug': self.lst.slug}))
        self.assertEquals(404, resp.status_code)

    def test_redirect_owned_list(self):
        """[#72] A request for a public list url should redirect to the editable version
        for the owner of that List"""
        self._login_and_own()
        self.lst.is_public = True
        self.lst.save()
        resp = self.client.get(reverse('list-detail', kwargs={'slug': self.lst.slug}))
        self.assertRedirects(resp, reverse('my-list-update', kwargs={'slug': self.lst.slug}))

    def test_redirect_owned_list_not_public(self):
        """[#72] A request for a public list url should redirect to the editable version
        for the owner of that List even if the list isn't `is_public`"""
        self._login_and_own()
        self.lst.is_public = False
        self.lst.save()
        resp = self.client.get(reverse('list-detail', kwargs={'slug': self.lst.slug}))
        self.assertRedirects(resp, reverse('my-list-update', kwargs={'slug': self.lst.slug}))

    def test_redirect_owned_page_not_owner(self):
        """[#72] A request for an owned, is_public List page by an anonymous user should redirect to the non-owner page"""
        self.lst.is_public = True
        self.lst.save()
        resp = self.client.get(reverse('my-list-update', kwargs={'slug': self.lst.slug}))
        self.assertRedirects(resp, reverse('list-detail', kwargs={'slug': self.lst.slug}))

    def test_redirect_owned_page_not_owner(self):
        """[#72] A request for an owned, is_public List page by a different user should redirect to the non-owner page"""
        self.lst.is_public = True
        self.lst.save()
        self.client.force_login(self.user)
        resp = self.client.get(reverse('my-list-update', kwargs={'slug': self.lst.slug}))
        self.assertRedirects(resp, reverse('list-detail', kwargs={'slug': self.lst.slug}))

    def test_favorite_adds_to_list(self):
        """[#75] When a Favorite is added, it should get or create a list for this user called Favorites"""
        fave_list = models.List.objects.get(title=models.List.FAVORITE_LABEL, owner=self.user)
        self.assertEquals(0, fave_list.images.count())
        fave = models.Favorite.objects.create(image=self.img1, user=self.user)
        self.assertEquals(1, fave_list.images.count())

    def test_favorite_removed_from_list(self):
        """[#75] When a Favorite is unfavorited, it should be removed from the Favorites list"""
        fave_list = models.List.objects.get(title=models.List.FAVORITE_LABEL, owner=self.user)
        fave = models.Favorite.objects.create(image=self.img1, user=self.user)
        self.assertEquals(1, fave_list.images.count())
        fave.delete()
        self.assertEquals(0, fave_list.images.count())        
