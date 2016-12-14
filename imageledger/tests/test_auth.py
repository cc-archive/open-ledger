import os
import logging

from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model

from imageledger import models
from imageledger.tests.utils import *

class TestAuth(TestImageledgerApp):

    def setUp(self):
        self.username = 'testuser'

    def test_delete_account_redirects(self):
        """The delete account endpoint should redirect to home when complete"""
        user = get_user_model().objects.create_user(self.username, password=self.username)
        self.client.force_login(user)
        resp = self.client.post(reverse('delete-account'))
        self.assertRedirects(resp, reverse('index'))

    def test_delete_account_deletes_user(self):
        """The delete account endpoint should delete the user account"""
        user = get_user_model().objects.create_user(self.username, password=self.username)
        self.assertEquals(1, get_user_model().objects.filter(username=self.username).count())
        self.client.force_login(user)
        self.client.post(reverse('delete-account'))
        self.assertEquals(0, get_user_model().objects.filter(username=self.username).count())

    def test_delete_account_deletes_lists(self):
        """The delete account endpoint should delete any of the user's lists"""
        user = get_user_model().objects.create_user(self.username, password=self.username)
        img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')
        lst = models.List.objects.create(title='test', owner=user)
        lst.images.add(img1)
        self.assertEquals(1, models.List.objects.filter(owner=user, title='test').count())
        self.client.force_login(user)
        self.client.post(reverse('delete-account'))
        self.assertEquals(0, models.List.objects.filter(owner=user).count())

    def test_delete_account_deletes_favorites(self):
        """The delete account endpoint should delete any of the user's favorites"""
        user = get_user_model().objects.create_user(self.username, password=self.username)
        img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')
        fave = models.Favorite.objects.create(image=img1, user=user)
        self.assertEquals(1, models.Favorite.objects.filter(user=user).count())
        self.client.force_login(user)
        self.client.post(reverse('delete-account'))
        self.assertEquals(0, models.Favorite.objects.filter(user=user).count())

    def test_delete_account_deletes_tags(self):
        """The delete account endpoint should delete any of the user's tags"""
        user = get_user_model().objects.create_user(self.username, password=self.username)
        img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')
        tag = models.Tag.objects.create(name='tag')
        fave = models.UserTags.objects.create(image=img1, user=user, tag=tag)
        self.assertEquals(1, models.UserTags.objects.filter(user=user).count())
        self.client.force_login(user)
        self.client.post(reverse('delete-account'))
        self.assertEquals(0, models.UserTags.objects.filter(user=user).count())
