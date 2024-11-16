import unittest

import lib

from werkzeug.test import Client
from werkzeug.wrappers import Response

import main


class Test(unittest.TestCase):

    def get(self, url):
        client = Client(main.app, Response)
        return client.get(url)

    def testHome(self):
        response = self.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Mikel's Home Page", response.text)
        self.assertIn('view my <a href="/resume">resume</a>', response.text)
        self.assertIn('<a href="/contact">contact me</a>', response.text)

    def testAbout(self):
        response = self.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertIn("About Mikel", response.text)

    def testContact(self):
        response = self.get('/contact')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Contact Mikel", response.text)
        self.assertIn("mikel@mikelward.com", response.text)

    @unittest.skip('/static/m.ico is not served by werkzeug app yet.')
    def testFavicon(self):
        response = self.get('/static/m.ico')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'image/x-icon')

    def testResume(self):
        response = self.get('/resume')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Mikel's Resume", response.text)

    @unittest.skip('/styles is not served by werkzeug app yet.')
    def testStyles(self):
        response = self.get('/styles/all.css')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/css')
        self.assertIn('font', response.text)

    def testMissing(self):
        response = self.get('/nosuch')
        self.assertEqual(response.status_code, 404)
        self.assertIn("That page doesn't exist.  Please use the menu",
                      response.text)
        self.assertIn('<a href="/contact">contact me</a>',
                      response.text)


if __name__ == '__main__':
    unittest.main()


#  vim: set ts=8 sw=4 tw=0 et:
