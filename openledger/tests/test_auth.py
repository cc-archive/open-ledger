import json

import responses
import jinja2

from flask import request, url_for

from openledger.views import auth_views
from openledger.tests.utils import *

class TestAuthAPI(TestOpenLedgerApp):

    def test_auth_api_not_logged_in(self):
        """The Auth API should return False for a user not logged in"""
        rv = self.client.get(url_for('logged_in'))
        assert 200 == rv.status_code
        assert not rv.json['logged-in']

    def test_auth_api_logged_in(self):
        """The Auth API should return True for a user who is logged in"""
        with self.client.session_transaction() as sess:
            sess[auth_views.AUTH_SESSION_IDENTIFIER] = 'test@example.com'
        rv = self.client.get(url_for('logged_in'))
        assert 200 == rv.status_code
        assert rv.json['logged-in']
