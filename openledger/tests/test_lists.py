import os
import unittest
import responses
import jinja2

from flask import request, url_for

from openledger import app as ol
from openledger.tests.utils import *

class TestListViews(TestOpenLedgerApp):

    def setUp(self):
        super().setUp()
        self.lst = models.List(title='test')
        self.img1 = models.Image(title='image title', url='http://example.com/1', license='CC0')
        self.img2 = models.Image(title='image title', url='http://example.com/2', license='CC0')
        self.lst.images = [self.img1, self.img2]
        self.add_to_db(self.lst, self.img1, self.img2)

    def test_view_list_detail(self):
        """It should be possible to view a list's information"""
        rv = self.client.get('/list/' + self.lst.slug)
        assert 200 == rv.status_code
        p = select_node(rv, '.t-list-title')
        assert self.lst.title == p.text.strip()

    def test_view_list_not_found(self):
        """A request to view a list that doesn't exist should 404"""
        rv = self.client.get('/list/notfound')
        assert 404 == rv.status_code

    def test_view_list_images(self):
        """A request to view a list should show its available images"""
        rv = self.client.get('/list/' + self.lst.slug)
        p = select_nodes(rv, '.t-image-result')
        assert 2 == len(p)

    def test_update_list(self):
        """A request to update a list via a POST request should update the list values"""
        desc = 'new desc'
        title = 'new title'
        rv = self.client.post('/list/' + self.lst.slug,
                              data={'description': desc,
                                    'title': title})
        assert desc == self.lst.description
        assert title == self.lst.title

    def test_update_list(self):
        """A request to update a list via a POST request should redirect to the list detail when done"""
        rv = self.client.post('/list/' + self.lst.slug,
                              data={'description': self.lst.description,
                                    'title': self.lst.title})
        self.assertRedirects(rv, url_for('list-view', slug=self.lst.slug))
