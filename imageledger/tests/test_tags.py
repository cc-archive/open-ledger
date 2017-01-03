import os
import logging

from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model

from imageledger import models
from imageledger.tests.utils import *

class TestTagsViews(TestImageledgerApp):

    def setUp(self):
        super().setUp()
        self.img1 = models.Image.objects.create(title='image1', url='http://example.com/1', license='CC0')
        self.img2 = models.Image.objects.create(title='image2', url='http://example.com/2', license='CC0')
        self.username = 'testuser'
        self.user = get_user_model().objects.create_user(self.username, password=self.username)

    def test_tag_view_owned(self):
        """A user should be able to view their own tag on a page"""
        tag = models.Tag.objects.create(name='My Tag')
        user_tag = models.UserTags.objects.create(tag=tag, image=self.img1, user=self.user)
        self.client.force_login(self.user)
        resp = self.client.get(reverse('my-tags-detail', kwargs={'slug': tag.slug}))
        self.assertEquals(200, resp.status_code)
        self.assertEquals(1, len(select_nodes(resp, '.image-result')))

    def test_tag_view_not_found(self):
        """A logged-in request for a tag that doesn't exist should 404"""
        self.client.force_login(self.user)
        resp = self.client.get(reverse('my-tags-detail', kwargs={'slug': 'notfound'}))
        self.assertEquals(404, resp.status_code)

    def test_tag_exists_but_not_logged_in(self):
        """[#131] An anon request for a tag should redirect to login"""
        tag = models.Tag.objects.create(name='My Tag')
        user_tag = models.UserTags.objects.create(tag=tag, image=self.img1, user=self.user)
        # no log in
        resp = self.client.get(reverse('my-tags-detail', kwargs={'slug': tag.slug}))
        self.assertEquals(302, resp.status_code)
