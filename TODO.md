# TODO

## Decisions needing review

Guesses made under autopilot, recorded so nothing decided without the
repository owner silently becomes permanent. Each says what was decided, what
the alternative was, and why it is reversible.

- [ ] **The Codex gate's two documented limitations are taken as-is.** The
      shared codex-review setup is installed unchanged, with both known gaps
      recorded in `mikelward/codex-review`'s `docs/CONSUMER.md` rather than
      fixed here: a fork pull request's head gets no `codex-review-check`, and
      the head-associated run of that check comes from its own `push` trigger,
      so a same-repository pull request could in principle supply a job of
      that name calling something else. The alternative was holding this
      conversion until both are closed upstream. Fork pull requests are not a
      case these repositories take, and the second has no configuration remedy
      available — GitHub's *Require workflows to pass before merging* is an
      organization-ruleset rule and these repositories are on a personal
      account. The three workflow files are byte-identical template copies, so
      a local edit would fail the pin either way.
      *Reversible:* entirely — re-copy `templates/` when a remedy lands. Both
      are written out in full there, including the implementable one: move the
      consumer comparison inside the sweep, whose definition comes from the
      default branch and so is out of a branch's reach.

## Run the suite in CI

This repository had no `.github/workflows/` at all before the codex-review
setup landed, so the three files it added are the only workflows here, and
`codex-review-check` is the only check a pull request gets. `make test`
(`python3 main_test.py`) runs on a developer's machine and nowhere else.

Worth doing before requiring anything else in the ruleset: a required check
that only proves the workflows match their templates says nothing about
whether the app works. It is a small job — install `requirements.txt`, run
`main_test.py` — and it needs a top-level `permissions: contents: read` block
when it is written, so that `check_consumer.py`'s sole-writer scan keeps
passing.

Two of the eight tests currently skip. Worth finding out why as part of the
same change, since a skip in CI reads as a pass.

## Add the ruleset settings the Codex gate expects

Three settings this repository's ruleset does not have yet, all explained in
the shared `docs/CONSUMER.md`: require `codex` (not `sweep`), require
`codex-review-check / codex-review-check`, and require branches to be up to
date before merging. Deliberately a follow-up — requiring a check in the same
change that installs it would block the change that installs it.

Note for whoever sets them: the default branch here is `master`, not `main`,
so the ruleset's target has to say so.

## Review and merge gates

- [ ] Add a CI gate (`ci.yml`) running whatever checks this repository
      supports, so the ruleset has a test gate to require — or record
      here that there is deliberately nothing to run.
- [ ] Verify the settings half of the fleet's bar — every repository
      works the same: comprehensive automated review, required merge
      gates, and auto-merge. A ruleset on the default branch requiring
      the gates, the `codex` status, conversation resolution and
      up-to-date branches, with the auto-merge setting enabled.
