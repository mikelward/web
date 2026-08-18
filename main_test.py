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

    def testSetupRedirect(self):
        response = self.get('/setup')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'],
                         'https://github.com/mikelward/scripts/raw/main/setup')

    def testMissing(self):
        response = self.get('/nosuch')
        self.assertEqual(response.status_code, 404)
        self.assertIn("That page doesn't exist.  Please use the menu",
                      response.text)
        self.assertIn('<a href="/contact">contact me</a>',
                      response.text)


class LanesPolicyTest(unittest.TestCase):
    """Tests for the CI lane policy, .github/lanes.conf.

    The engine (mikelward/lanes) is tested in its own repository; what it
    cannot test is this repo's policy, whose failure mode is the quiet one: a
    broadened rule makes classify and gate derive the same wrong docs verdict,
    so `make test` skips under a green required check. The shape pin below is
    the real guard — editing a rule fails it, forcing this file to move in the
    same review — and the classification cases keep both directions honest.
    The matcher translates only the pinned pattern forms (`<dir>/**` and
    `**/*.<ext>`, per the lanes README: `*` never crosses `/`, `**` does); an
    unpinned form fails the test rather than being guessed at.
    """

    def parse(self):
        rules = []
        directives = {}
        with open('.github/lanes.conf') as f:
            for raw in f:
                line = raw.split(' #')[0].strip()
                if not line or line.startswith('#'):
                    continue
                word, rest = line.split(None, 1)
                if word in ('docs', 'code'):
                    rules.append((word, rest))
                else:
                    directives[word] = rest.split()
        return rules, directives

    def matches(self, path, pattern):
        if pattern.endswith('/**'):
            return path.startswith(pattern[:-2])
        if pattern.startswith('**/*.') and '/' not in pattern[3:]:
            return path.rsplit('/', 1)[-1].endswith(pattern[4:])
        self.fail('pattern %r is not a form this matcher covers — '
                  'teach it the new form along with the policy edit' % pattern)

    def classify(self, path):
        rules, _ = self.parse()
        for verdict, pattern in rules:
            if self.matches(path, pattern):
                return verdict
        return 'code'

    def testPolicyShape(self):
        rules, directives = self.parse()
        self.assertEqual(rules, [('code', 'templates/**'),
                                 ('code', 'static/**'),
                                 ('code', 'styles/**'),
                                 ('docs', '**/*.md')])
        self.assertEqual(directives['prefixes'], ['docs'])
        self.assertEqual(directives['dispatch-without-pr'], ['refuse'])

    def testMarkdownOutsideShippedTreesIsDocs(self):
        for path in ('AGENTS.md', 'TODO.md', 'docs/notes.md'):
            self.assertEqual(self.classify(path), 'docs', path)

    def testEverythingServedOrExecutedIsCode(self):
        for path in ('main.py', 'lib.py', 'app.yaml', 'Makefile',
                     'requirements.txt', 'templates/home.html',
                     'templates/notes.md', 'static/logo.png',
                     'styles/all.css', '.github/workflows/ci.yml',
                     '.gitignore'):
            self.assertEqual(self.classify(path), 'code', path)


if __name__ == '__main__':
    unittest.main()


#  vim: set ts=8 sw=4 tw=0 et:
