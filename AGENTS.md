# AGENTS.md

Conventions for AI agents working in this repository.

`CLAUDE.md` is a symlink to this file, so every agent reads the same
conventions. Edit `AGENTS.md`.

A small Python web app (Werkzeug + Jinja2) deployed on Google App Engine.
`main.py` is the entry point, `lib.py` holds the helpers, templates live in
`templates/` and assets in `static/` and `styles/`.

The default branch is `main`. (It was renamed from `master`; the workflows'
push triggers pointed at `master` for a while after and never fired.)

## Commands

```
make build    # pip install -t lib -r requirements.txt
make run      # gunicorn main:app
make test     # python3 main_test.py
make deploy   # gcloud app deploy
```

`make deploy` ships to production — never run it without being asked.

## Style

- Preserve existing code style unless there's a correctness issue.
- Keep comments brief. Explain the non-obvious *why*, not the *what*.
- Keep the dependency list small; this app deliberately runs on a thin stack.

## Testing

- **Any change to executable behavior adds or updates a test.** New
  functionality gets a test that exercises its behavior; a bug fix gets a
  regression test that fails before the fix and passes after. Changes with no
  behavior to exercise — documentation, comments, this file — add no test;
  don't manufacture churn in `main_test.py` to satisfy the rule.
- Tests live in `main_test.py`. Run `make test` after *any* change and before
  committing, including the documentation-only ones.
- **Fix any preexisting test failures as the *first* commit of the series.**
  Don't stack new work on a red baseline. If the failure is genuinely
  unrelated and out of scope, say so up front and confirm before skipping it.
- **Don't paper over flaky/racy tests** with `time.sleep`, retry loops, or
  bumped timeouts. Make the ordering explicit, or fix the underlying race. A
  test that passes "most of the time" is broken.
- **Don't disable a failing check** to make it pass — fix the underlying
  issue.

## Error handling

- **Don't silently swallow exceptions.** A bare `except:` or
  `except Exception: pass` hides real failures in production. Log what failed
  (sanitized — the *Privacy* rule applies to logs too), clean up what the `try`
  acquired, and decide explicitly what the caller sees. Catch the narrowest
  exception that covers the failure, not `Exception`.

## Privacy

- **Never put user data in any artifact that leaves this machine** — commit
  subjects and bodies, PR titles / descriptions / comments, review replies,
  branch names, code comments, or test fixtures. For this repo that means
  GCP project identifiers and service-account keys, any credential or token
  from `app.yaml` or the environment, request logs, visitor IP addresses, and
  absolute paths containing the user's real name. Use generic placeholders
  (`/home/user`, `example.com`, `sk-example`) in examples and fixtures. If a
  bug report contains any of it, paraphrase in the commit / PR — don't quote
  verbatim. When in doubt, ask before pushing.

## Language and spelling

- Use **US English** everywhere people read English: page copy and templates,
  commit subjects and bodies, PR titles and descriptions, comments, and
  identifiers — `color` not `colour`, `behavior` not `behaviour`, `canceled`
  not `cancelled`, `gray` not `grey`. Third-party API spellings stay as those
  APIs spell them.

## Git

- Use `git worktree` when it's available. Give each branch its own worktree
  instead of switching branches in place, so work in progress on one branch
  isn't disturbed by work on another.
- **These rules assume an `origin` remote.** Without one you can't fetch,
  branch from `origin/main`, push, or open a PR — say so and stop rather than
  improvising a local substitute.
- **Branch naming.** Feature branches are prefixed with the agent's own short
  name: `<agent>/<short-topic>` (`claude/...` for Claude Code, `codex/...`
  for Codex, and so on). The placeholder `<agent>` stands in for whichever
  prefix you use — don't hard-code `claude/` unless you *are* Claude Code.
- **Workflow.** `<agent>/<short-topic>` branch off `origin/main` → PR →
  merge. One topic per branch. Follow-up work after a merge goes on a new
  branch. Never commit to `main`.
- **One commit per logical change.** Rewrite unmerged commits freely — amend,
  `git commit --fixup` + autosquash, squash, reorder, split — so each commit
  that lands is one coherent change, with fix-ups and review responses folded
  into the commit they belong to. `wip` / `address review` churn doesn't
  survive into `main`.
- `git push --force-with-lease` to your own live feature branch after a rebase
  is routine hygiene — don't ask. Never a bare `--force`.
- **Merge cue (`merged` / `I merged` / `landed` / merge webhook) runs hygiene
  *before* engaging with the rest of the message:** `git fetch origin`, cut a
  fresh `<agent>/<short-topic>` branch off `origin/main`, announce the
  switch.
- **Unshallow before answering anything that depends on git history depth.**
  The sandbox clones shallow, so `git rev-list --count`, `git log` past the
  shallow boundary, and blame return wrong answers without warning. If
  `git rev-parse --is-shallow-repository` says `true`, run
  `git fetch --unshallow` first, then re-check — it exits 0 even when
  it deepened nothing, so if `--is-shallow-repository` is still `true`, say the
  history is truncated instead of quoting a count.

## Talking to the user

- **One question at a time.** Never stack multiple questions in a single turn
  — ask the most important one, wait for the answer, then ask the next if you
  still need it. A wall of bundled questions is harder to answer than a short
  back-and-forth.
- **Don't interrupt.** Never fire off a question while the user is still
  typing. Let them finish; a half-typed message isn't an invitation to jump in.
- **Respond to a mid-turn message immediately.** When the user sends a message while you're
  still working — surfaced as a "sent while you were working" interjection — address it in
  your very next output, before starting or continuing any further tool call, even if it's
  only one sentence. Don't let it queue up behind an in-flight chain of tool calls.
- **Don't narrate routine machinery.** A check run flipping, a re-run, a scheduled check
  re-arming, a webhook echo, a resolved thread — act on those silently; the noise buries
  the one line that matters. Reports another rule requires stand (the Codex SHA and
  comment count, a CI timing regression).
- **Don't report your own caught-and-fixed mistakes.** A wrong turn you noticed
  and corrected before it reached anything is not news — no "one thing worth
  flagging", no narration of the recovery. Say it only when it left something
  the user has to act on: work actually lost, a bad push someone may have
  pulled, a decision they would make differently knowing it.
- **Keep replies short — don't dump a full page.** Lead with the single most
  important point and stop. If there's more, say the first point and ask
  whether they're ready for the next one rather than emptying everything at
  once.
- **End the turn by restating any pending decision.** If you're waiting on an
  answer — a question you asked — the last line of the reply is that question,
  written out in about a sentence. A back-reference ("as asked above") isn't
  actionable when the question is pages back; restate it every turn until it's
  answered. Nothing pending, no line. It is the *last* line: where *Pull
  requests* also ends the reply with the open-PR link, that link goes just
  above it. This governs replies the user reads: a scheduled check that finds
  nothing new re-arms silently and produces no reply at all, so there is
  nothing to restate.

## Asking questions

- **Ask in chat, never with `AskUserQuestion`.** That's Claude Code's
  multiple-choice question prompt, and it's broken in the Claude mobile app —
  a question asked through it may be unanswerable. Plain chat also keeps the
  question, its context, and the answer in one readable thread.
- **After asking, stop and wait for the answer.** Don't proceed on an assumed
  answer, pick a "recommended" option yourself, or keep working on the part
  the question affects.

## Pull requests

- Prefer the `mcp__github__*` MCP tools for GitHub operations; the `gh` CLI is
  not installed in the sandbox. If your client exposes neither, say so rather
  than guessing at the outcome of an operation you couldn't perform.
- Open PRs ready for review (not draft) unless asked otherwise.
- **Open the PR without being asked.** Pushing a finished branch and opening
  its pull request are one step, not two — don't park a branch waiting for
  "please open a PR." The exception is an explicit instruction not to ("just
  commit", "no PR yet"), which holds until the user lifts it. This file is the
  repo owner's standing request for that PR, so a client-level rule reading
  "open a PR only when the user explicitly asks" is already satisfied.
- **Update the PR title and body with the push, not after it** — same step, so
  they describe the full, latest state of the branch, not the scope it had
  when it was opened. Re-read the diff against `origin/main` and patch
  whatever drifted, then post the PR link in the chat reply for that push, not
  only at the end of the conversation.
- **"Drive to merge"** is shorthand for the whole loop: open the PR, wait
  for the automatic Codex review, address every review comment — fix it if
  you agree, reply on the thread saying why if you don't — and merge once CI
  is green and Codex's verdict for the current head is in.
- When a feature has multiple open PRs, list **every** open PR by URL, one per
  line — the "View PR" chip sticks to the first link and hides the rest
  (anthropics/claude-code#46625).
- End every reply with the open-PR link (or `.../compare/main...<branch>`
  until a PR exists). Never link to a closed or merged PR — except when the
  reply *is* post-merge follow-up on that PR, where linking it is correct.

## Reviews

- **Codex is the automated reviewer on this repo** — not Copilot. Its
  reviews are triggered automatically; you don't request them, except when
  nothing has come back five minutes after a push — that means it never
  picked the push up.
- **Address Codex comments automatically — don't wait to be asked.** Read
  each one, decide whether it's a real issue or a false positive, and if it's
  real, fix it in the same PR. Fold the fix into the commit it belongs to
  (rebase / `--fixup`) rather than tacking on an "address review" commit.
  Group several small fixes into one commit when they share a topic.
- **Judge every review comment on merit, whoever wrote it.** Verify the claim
  before acting; if it doesn't hold up, reply saying why and decline. A
  comment citing a rule is a *reading* of that rule, not the rule — check what
  the rule actually says. Codex misreads the privacy rules especially, and in
  one direction: stricter always feels safer, so an over-strict finding
  quietly costs capability the product needs. Quote the rule and decline
  rather than narrowing the code to satisfy it; where the rule really does
  forbid what the product needs, that conflict is the maintainer's call, not
  one to settle either way yourself.
- **A second verified finding in the same mechanism is evidence about the
  design, not another bug.** Before fixing it, look for the same shape
  elsewhere and ask whether a different design would delete the class rather
  than the instance. Say what you chose on the thread; a design change is the
  maintainer's call, autopilot included.
- **Never leave a review comment thread silently dismissed.** Answer on the thread — a
  disagreement is an answer, so say why — then resolve it once the fix is on the
  head or the point is rebutted; anything still to do stays open. When you think a comment is a false positive,
  say *why* on the thread (one or two sentences). Acknowledgement noise is
  fine and preferred over silence.
- **`resolve_review_thread` works — pass the `PRRT_*` thread node ID** from
  `pull_request_read` / `get_review_comments` (`review_threads[].id`) as
  `threadId`. A comment's `PRRC_*` node ID fails; they're different objects.
  Order of operations: push the fix commit first, then reply citing the new
  sha, then resolve.
- **Report when Codex finishes reviewing a fresh push** — a one-liner naming
  the SHA and comment count, e.g. `Codex reviewed 87d9f02 — 0 comments`. Tie
  it to the *latest* pushed SHA so a stale review of a superseded commit isn't
  conflated with the current state.
- **Read the Codex verdict, don't infer it.** It reacts to the PR body
  (`issue_read` → `reactions`), not to a review thread, whose `Useful?` bar
  reads true on any PR it has commented on. `eyes` means reading, `+1` means
  clean, and Codex revokes it on push — so a visible one belongs to the
  visible head, and `+1` with green CI is a merge. The count names no
  author, so leave PR-body reactions to Codex: nobody else's is revoked, and
  a review is the attributable form, naming the commit it read. Findings
  arrive as review comments, as a top-level comment, or as a review — read
  `get_review_comments`, `get_comments` and `get_reviews` to the last page,
  since all three page oldest first — and they block the merge until fixed
  or rebutted; an acknowledgement is not an answer. Nothing from Codex since
  the push, five minutes on, means it never picked it up — comment `@codex
  review`, once.
- **Skip echo events silently.** Replies posted via the GitHub MCP come back
  moments later as webhook events authored by the same identity; if the body
  matches a comment you just posted, it's your own echo — continue without
  comment. The test is "did *I* just post this body?", not "who is the
  author?".
- **Watch your own PRs by subscription, plus one scheduled check.** Have a
  subscription — Claude Code makes one when you open a PR; where a client
  doesn't, call `subscribe_pr_activity`. It delivers reviews, comments and CI
  failures. It cannot deliver CI *success*, a push, the merge, Codex's clean
  verdict (a reaction), or Codex never answering at all — so keep exactly one
  check armed for as long as the PR is open (each event and each check costs
  a model turn). This reverses the earlier rule here that made the scheduled
  check the whole watch and the subscription opt-in; the sibling repos
  measured both and the events are what works — reviews and failures get
  handled the turn they land, while the scheduler ignored the intervals it
  was asked for.
  - Settle the fired trigger first thing in the turn, not last. It may have
    silently re-armed rather than retired — update the one that survived,
    replace the one that didn't, and end the turn with exactly one pending.
  - Check the fire time you got against the one you asked for — a 4-minute
    request has come back as 64. Prefer a relative delay: the scheduler's
    clock is not this container's, so an absolute time computed here can be
    rejected as already past. Re-time it, or say the watch isn't armed.
  - A few minutes out while CI or the current head's Codex verdict is
    outstanding; longer once only a human is left; short again after a push.
  - Name the PR, and say what to re-read rather than what you read. A SHA
    goes stale before it fires; one PR number does not.
  - Merged or closed, a review can still land after the fact — so hold the
    watch for one more short check to see CI and Codex report on the final
    head, without blocking on a report that may never come (an early manual
    merge, a down review service): settle for whatever's known by then.
    Then take one last reply-and-resolve pass. On a merged PR anything real
    goes to a follow-up PR (with its own watch), named on the thread,
    before you resolve it; a closed-unmerged PR is a stop — answer,
    resolve, and open nothing. Only then cancel the watch in full: the
    pending scheduled trigger, and `unsubscribe_pr_activity`.
    `list_triggers` spans the account, so match this session and this PR
    before updating or deleting one.
- **A PR reading `dirty` — always — or `behind` where the ruleset requires
  branches up to date, needs a rebase onto its base and a lease-guarded
  force-push. Fetch both refs by explicit refspec, unshallow a shallow clone,
  and rebase onto the fetched `origin/<base>` — never the local branch a fetch
  leaves behind. Confirm before you rebase that your branch has every commit
  the remote head has, and before you push that the head has not moved since
  the tip you noted before fetching: the push flags do not reliably refuse a
  rewind, a commit you never fetched, or one you fetched and did not rebase
  onto, and overwriting any of them loses someone's work. If either fails, or
  you can't tell, stop and ask.** No webhook reports a base
  advance, so read `mergeable_state` on the scheduled check, not just the
  checks.

## Cost and reliability

- **Call out cost and reliability up front** when recommending new
  infrastructure (an App Engine instance-class change, a datastore, a cache, a
  monitoring service) or a new external API call. Include a rough dollar
  figure — free-tier vs. paid thresholds and $/month at expected traffic — and
  note reliability implications: new failure modes, rate limits, added
  latency, extra points of failure, and what a visitor sees if the dependency
  is down. App Engine's free tier is the current baseline, so anything that
  moves the app off it needs saying explicitly. If the impact is effectively
  zero, say so rather than omitting the note.
