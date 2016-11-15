import os
import logging

from django.urls import reverse
from django.conf import settings

from imageledger.tests.utils import *

class TestListViews(TestImageledgerApp):

    def setUp(self):
        super().setUp()
        self.lst = models.List.objects.create(title='test')
        self.img1 = models.Image.objects.create(title='image title', url='http://example.com/1', license='CC0')
        self.img2 = models.Image.objects.create(title='image title', url='http://example.com/2', license='CC0')
        self.lst.images.add(self.img1)
        self.lst.images.add(self.img2)
        
    def test_view_list_detail(self):
        """It should be possible to view a list's information"""
        resp = self.client.get('/list/' + self.lst.slug)
        assert 200 == resp.status_code
        p = select_node(resp, '.t-list-title')
        assert self.lst.title == p.text.strip()

    def test_view_list_not_found(self):
        """A request to view a list that doesn't exist should 404"""
        resp = self.client.get('/list/notfound')
        assert 404 == resp.status_code

    def test_view_list_images(self):
        """A request to view a list should show its available images"""
        resp = self.client.get('/list/' + self.lst.slug)
        p = select_nodes(resp, '.t-image-result')
        assert 2 == len(p)

    def test_update_list(self):
        """A request to update a list via a POST request should update the list values"""
        desc = 'new desc'
        title = 'new title'
        resp = self.client.post('/list/' + self.lst.slug,
                              {'description': desc,
                                    'title': title})
        assert desc == self.lst.description
        assert title == self.lst.title

    def test_update_list(self):
        """A request to update a list via a POST request should redirect to the list detail when done"""
        resp = self.client.post('/list/' + self.lst.slug,
                              {'description': self.lst.description,
                                    'title': self.lst.title})
        self.assertRedirects(resp, reverse('list-update', kwargs={'slug': self.lst.slug}))
