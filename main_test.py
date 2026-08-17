import os
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


class Workflows(unittest.TestCase):
    """Tests for the codex-review workflows.

    The sweep's own logic and tests live in mikelward/codex-review; what is
    pinned here is the part that stays in a consumer repository: which events
    may run a status-writing job, and what token it holds. Each of these
    guards a value whose wrong setting produces no error at all -- just a
    merge gate that quietly stops working, or one that can never clear.

    Read as patterns over YAML, which is an approximation of YAML and known
    to be. It is worth it because the alternative is a YAML parser this app
    has no reason to depend on; the risk is bounded by these being pins on
    exact strings that a human wrote and a human will edit.

    Every match runs against a comment-stripped copy, and the settings that
    live in a block are matched inside that block. Those headers explain each
    setting at length, in the setting's own words -- `statuses: write`
    appears in six comments of codex-review.yml, `pull_request_review` in the
    listener's -- so a whole-file match would keep passing on the prose after
    the setting it describes was deleted.
    """

    WORKFLOWS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             '.github', 'workflows')
    SWEEP = 'codex-review.yml'

    def raw(self, name):
        """A workflow's text, comments and all.

        Only the assertion pinning a warning in the header wants this.
        """
        with open(os.path.join(self.WORKFLOWS, name), encoding='utf-8') as f:
            return f.read()

    def read(self, name):
        """A workflow with whole-line and trailing comments dropped.

        A value keeps whatever precedes the `#`, so this can only ever remove
        prose, never a setting.
        """
        return '\n'.join(line.split('#')[0].rstrip()
                         for line in self.raw(name).splitlines())

    def block(self, key):
        """The body of a top-level block in the sweep.

        Everything after `<key>:` at column 0, up to the next line starting at
        column 0. Stripped comments leave blank lines, which stay inside the
        block and match nothing.
        """
        body = []
        inside = False
        for line in self.read(self.SWEEP).splitlines():
            if line == key + ':':
                inside = True
                continue
            if inside and line[:1] not in ('', ' ', '\t'):
                break
            if inside:
                body.append(line)
        return '\n'.join(body)

    def triggers(self):
        """The sweep's `on:` block alone.

        The header above it explains at length why `workflow_dispatch` and a
        bare `pull_request` are absent, so a whole-file scan for those names
        matches the prose and passes while saying nothing about the triggers.
        """
        return self.block('on')

    def testExtractedBlocksFound(self):
        # Both extractions would pass vacuously on an empty string, taking
        # every assertion that reads them with it.
        self.assertIn('pull_request_target:', self.triggers())
        self.assertIn('contents: read', self.block('permissions'))

    def testSweepRunsTheSharedActionAndChecksNothingOut(self):
        # `@main` is deliberate: the action has no build step and no
        # dependencies, so the file that runs is the file you can read. No
        # checkout, also deliberate -- it would put a token-bearing
        # .git/config within reach of a job that can write commit statuses.
        sweep = self.read(self.SWEEP)
        self.assertIn('uses: mikelward/codex-review@main', sweep)
        self.assertNotIn('actions/checkout', sweep)

    def testSweepStartsOnEveryEventThatCanChangeTheVerdict(self):
        # `edited` is load-bearing: retargeting a pull request changes the
        # reviewed diff without moving the head SHA, and GitHub emits
        # `edited` rather than `synchronize` for it, so an existing
        # `codex: success` would stand over a diff nothing had read.
        on = self.triggers()
        self.assertIn(
            'types: [opened, reopened, ready_for_review, synchronize, '
            'edited, closed]', on)
        self.assertIn('workflows: [codex-review-listener]', on)

    def testSweepStartsOnNoEventThatLetsABranchSupplyItsOwn(self):
        # `workflow_dispatch` takes a ref and runs the file FROM that ref; a
        # bare `pull_request` has the same hole via the merge ref; and
        # `pull_request_review` is merge-ref too, which is why it lives on
        # the unprivileged listener instead.
        on = self.triggers()
        self.assertNotIn('workflow_dispatch', on)
        self.assertNotIn('  pull_request:', on)
        self.assertNotIn('  pull_request_review:', on)

    def testSweepKeepsItsLoopEnvelopeAndHourlyBackstop(self):
        # A canceled loop is a gate that stopped sweeping mid-review; 65
        # minutes caps a hung API call ten past the action's 55-minute loop.
        self.assertIn("cron: '23 * * * *'", self.triggers())
        sweep = self.read(self.SWEEP)
        self.assertIn('cancel-in-progress: false', sweep)
        self.assertIn('timeout-minutes: 65', sweep)

    def testSweepJobIsNamedAndIsNotARequiredCheck(self):
        # Pinned so the header's reasoning keeps naming a job that exists --
        # NOT because a ruleset requires it. Requiring `sweep` is unsafe: a
        # concurrency group holds one pending run, so a head-associated run
        # queued behind a long sweep is canceled and its replacement reports
        # against the default branch, leaving the head with a required check
        # that can never clear.
        self.assertIn('\n  sweep:\n', self.read(self.SWEEP))
        # The one assertion that wants the raw file: it pins the warning.
        self.assertIn('DO NOT REQUIRE `sweep`', self.raw(self.SWEEP))

    def testListenerHoldsNothingAndIsNamedAtBothEnds(self):
        # Renaming one end without the other severs the relay silently, and a
        # verdict submitted as a review with no inline comments goes unheard.
        listener = self.read('codex-review-listener.yml')
        self.assertIn('name: codex-review-listener', listener)
        self.assertIn('pull_request_review:', listener)
        self.assertIn('permissions: {}', listener)

    def testSweepIsTheOnlyWorkflowThatCanWriteStatuses(self):
        # A commit status belongs to the SHA, so a second writer is an
        # unordered write: one delayed past this run's exit overwrites a
        # fresh verdict with a stale one, and nothing reports that it
        # happened.
        #
        # Refusing the literal `statuses: write` in the other files is not
        # enough, and both holes are silent. `permissions: write-all` is
        # valid YAML that grants the scope without ever spelling it; and a
        # workflow with NO permissions block inherits the repository's
        # default GITHUB_TOKEN permission -- a repository setting, which no
        # file here can see, and which may be read/write. So each other
        # workflow has to declare its own grant, name no status scope at all
        # (none needs even `statuses: read`, and asking for the key rather
        # than one spelling of its value settles the quoting question too),
        # and take no blanket grant.
        #
        # The sweep is asked about its permissions block; the others about
        # their whole file, since a job-level grant is indented and a
        # top-level scan would miss it. Only the top-level `permissions:`
        # counts as declaring one, though: a job-level block leaves every
        # other job on the repository default.
        perms = self.block('permissions')
        self.assertIn('statuses: write', perms)
        self.assertNotIn('write-all', self.read(self.SWEEP))
        # ...and the status is the only thing the sweep may write.
        self.assertEqual(1, sum(': write' in line
                                for line in perms.splitlines()))
        names = [n for n in os.listdir(self.WORKFLOWS)
                 if n.endswith(('.yml', '.yaml'))]
        # The scan passes vacuously over an empty directory, so prove it had
        # the sweep and at least one other file to distinguish.
        self.assertGreaterEqual(len(names), 2, names)
        for name in names:
            if name == self.SWEEP:
                continue
            text = self.read(name)
            self.assertTrue(
                any(line.startswith('permissions:')
                    for line in text.splitlines()),
                '%s must declare a top-level permissions block' % name)
            self.assertNotIn('statuses:', text,
                             '%s must ask for no status scope' % name)
            self.assertNotIn('write-all', text,
                             '%s must take no blanket grant' % name)


if __name__ == '__main__':
    unittest.main()


#  vim: set ts=8 sw=4 tw=0 et:
