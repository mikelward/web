import re
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


class WorkflowCheckRenameTest(unittest.TestCase):
    """Guards the temporary state while renaming the required check from
    `gate` to `lanes` (mikelward/lanes#9): a duplicate job, kept in sync by
    hand until the ruleset is flipped and `gate` is deleted. Nothing else
    pins the two jobs together, so a hand edit to one that forgets the other
    would drift silently -- exactly the false-pass failure mode this suite
    is meant to catch.

    Read as regexes over YAML, same tradeoff LanesPolicyTest makes above: a
    real parser is unnecessary weight for pinning exact strings a human
    wrote and a human will edit.

    Delete this class along with the `gate` job once the ruleset requires
    only `lanes` -- it exists to guard the overlap window, not the steady
    state.
    """

    def setUp(self):
        with open('.github/workflows/ci.yml') as f:
            self.workflow = f.read()

    def jobBlock(self, key):
        marker = '\n  %s:\n' % key
        start = self.workflow.find(marker)
        self.assertNotEqual(start, -1, 'job "%s" not found in ci.yml' % key)
        rest = self.workflow[start + 1:]
        after_key_line = rest[rest.find('\n') + 1:]
        m = re.search(r'\n {2}\S', after_key_line)
        if m is None:
            return self.workflow[start + 1:]
        end = start + 1 + rest.find('\n') + 1 + m.start()
        return self.workflow[start + 1:end]

    def testBothJobsExistWhileTheRenameIsInFlight(self):
        self.assertRegex(self.workflow, r'\n {2}gate:\n {4}name: gate\n')
        self.assertRegex(self.workflow, r'\n {2}lanes:\n {4}name: lanes\n')

    def testGateAndLanesRunIdenticallyApartFromTheirOwnName(self):
        def strip(block):
            return re.sub(r'^ {2}\S+:\n {4}name: \S+\n', '', block)
        self.assertEqual(
            strip(self.jobBlock('gate')), strip(self.jobBlock('lanes')),
            'the gate and lanes jobs have drifted -- keep them identical '
            'until gate is deleted')


class ZizmorWorkflowTest(unittest.TestCase):
    """Tests for the required zizmor scan, .github/workflows/zizmor.yml.

    Required (once the ruleset lists it -- see TODO.md) means a malformed
    policy or a broken invocation blocks every merge, so these guard the
    triggers and the pin as tightly as the workflow's own header explains.
    Read with plain string matching, not a YAML parser, matching
    main_test.py's other conventions.
    """

    def workflow(self):
        with open('.github/workflows/zizmor.yml') as f:
            return f.read()

    def testPinsTheZizmorVersionExactly(self):
        # An unpinned run takes whatever release is newest, and a new release
        # adds audits -- bumping the pin should be a deliberate edit that
        # re-reads the findings, never a side effect.
        self.assertIn('pipx run --spec zizmor==1.29.0 zizmor', self.workflow())

    def testScansOffline(self):
        self.assertIn(' --offline', self.workflow())

    def testHoldsReadOnlyPermissions(self):
        workflow = self.workflow()
        self.assertIn('\npermissions:\n  contents: read\n', workflow)
        self.assertEqual(workflow.count('\npermissions:'), 1)

    def testRunsOnTheDefaultBranch(self):
        # This repo's default branch is master, not main (AGENTS.md) -- a
        # push filter naming main would silently never fire.
        self.assertIn('branches: [master]', self.workflow())

    def testHasNoPathsFilter(self):
        # A workflow filtered by paths creates NO check run at all on a
        # non-matching pull request (unlike a skipped job, which reports
        # "skipped" and satisfies a ruleset) -- fatal once `zizmor` is
        # required, so the filter must be gone from both triggers. The
        # header comment still discusses the filter in prose, so match the
        # actual YAML key rather than a bare substring.
        self.assertNotIn("paths: ['.github/**']", self.workflow())

    def testPullRequestRunsOnEditedToo(self):
        # The default `pull_request` type set lacks `edited`: a retarget
        # regenerates the merge ref against the new base while the head --
        # and the green check already attached to it -- stays put, so
        # without `edited` the old target's scan would satisfy the new one
        # unexamined.
        self.assertIn(
            'types: [opened, synchronize, reopened, edited]',
            self.workflow())


if __name__ == '__main__':
    unittest.main()


#  vim: set ts=8 sw=4 tw=0 et:
