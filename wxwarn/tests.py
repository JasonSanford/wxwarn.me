from django.utils import unittest
from django.test.client import Client


class TestHome(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def test_details(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Get notifications for severe weather' in response.content)


class TestUserNoAuthGetsRedirect(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def test_details(self):
        response = self.client.get('/user/')
        print response

        self.assertEqual(response.status_code, 302)
