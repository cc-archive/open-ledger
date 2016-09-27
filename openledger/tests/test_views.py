from openledger import app
import unittest

class TestViews(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_index(self):
        """The home page should load without errors"""
        rv = self.app.get('/')
        assert rv
