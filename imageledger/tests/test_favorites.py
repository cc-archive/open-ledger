import os
import logging

from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model

from imageledger import models
from imageledger.tests.utils import *

class TestFavoritesViews(TestImageledgerApp):

    def setUp(self):
        super().setUp()
        self.img1 = models.Image.objects.create(title='image1', url='http://example.com/1', license='CC0')
        self.img2 = models.Image.objects.create(title='image2', url='http://example.com/2', license='CC0')
        self.username = 'testuser'
        self.user = get_user_model().objects.create_user(self.username, password=self.username)
        self.client.force_login(self.user)

    def test_favorites_shown(self):
        """When an image is favorited, it should show up on the My Lists page"""
        models.Favorite.objects.create(user=self.user, image=self.img1)
        models.Favorite.objects.create(user=self.user, image=self.img2)
        resp = self.client.get(reverse('my-lists'))
        self.assertEqual(2, len(select_nodes(resp, '.t-image-result')))
        assert 'image1' in str(resp.content)
        assert 'image2' in str(resp.content)

    def test_favorites_removed(self):
        """When a favorite is removed, it should not appear on the My Lists page"""
        fave = models.Favorite.objects.create(user=self.user, image=self.img1)
        resp = self.client.get(reverse('my-lists'))
        self.assertEqual(1, len(select_nodes(resp, '.t-image-result')))
        fave.delete()
        resp = self.client.get(reverse('my-lists'))
        self.assertEqual(0, len(select_nodes(resp, '.t-image-result')))
