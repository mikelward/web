---
trigger: always_on
alwaysApply: true
last_modified: 2026-10-23
---

# AGENTS.md

`CLAUDE.md` and `GEMINI.md` are symlinks to this file. Edit `AGENTS.md` and bump
`last_modified`.

**At the start of every session, print the full absolute path of the `AGENTS.md` you
loaded and its `last_modified` date**, so a stale or wrong copy is caught first.

A small Python web app (Werkzeug + Jinja2) on Google App Engine: `main.py` is the entry
point, `lib.py` the helpers, `templates/` the templates, `static/` and `styles/` the
assets. The default branch is `main` (renamed from `master`, so a trigger still naming
`master` never fires).

Keep this file short — one-liners over essays, **under 24,000 bytes** (`wc -c AGENTS.md`):
Antigravity caps rule files at 24 KB and silently truncates the tail. State the rule and
the failure it prevents; incident narratives belong in commits. Add a rule the first time
something bites, rewrite/trim rather than append, and delete rules that stopped biting.

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
- Keep comments brief: the non-obvious *why*, not the *what*.
- Keep the dependency list small; this app deliberately runs on a thin stack.

## Testing

- **Any change to executable behavior adds or updates a test** in `main_test.py`: new
  behavior gets one, a bug fix gets a regression test that fails before and passes after.
  Docs, comments and this file add none — no manufactured churn.
- **Run `make test` after *any* change and before committing**, docs-only included.
- **Fix preexisting test failures as the first commit**; if one is genuinely unrelated,
  say so up front and confirm before skipping it. **No `time.sleep`, retries, or bumped
  timeouts** for flaky/racy tests — make the ordering explicit or fix the race. **Never
  disable a failing check.**

## Error handling

- **Don't silently swallow exceptions.** No bare `except:` or `except Exception: pass`.
  Log what failed (sanitized — *Privacy* applies to logs), clean up what the `try`
  acquired, decide explicitly what the caller sees, and catch the narrowest exception
  that covers the failure, not `Exception`.

## Privacy

- **Never put user data in any artifact leaving this machine** (commits, PRs, replies,
  branch names, code comments, fixtures): GCP project identifiers and service-account
  keys, any credential or token from `app.yaml` or the environment, request logs, visitor
  IP addresses, absolute paths containing the user's real name. Use placeholders
  (`/home/user`, `example.com`, `sk-example`); paraphrase bug reports; when in doubt, ask
  before pushing.

## Language and spelling

US English everywhere people read it (page copy, templates, commits, PRs, comments,
identifiers): `color`, `behavior`, `canceled`, `gray`. Third-party API spellings stay.

## Git

- **Assumes an `origin` remote**; without one, say so and stop rather than improvising.
  Use `git worktree` when available, one per branch.
- Feature branches: `<agent>/<short-topic>` (`claude/…` Claude Code, `gemini/…` Gemini /
  Antigravity, `codex/…` Codex) off `origin/main` → PR → merge; one topic per branch, a
  new branch for follow-up after a merge, never commit to `main`. Don't hard-code
  `claude/` unless you are Claude Code.
- **Your `<agent>/` branches are yours** — create, push, `--force-with-lease` the ones
  this session created or was assigned (this file is the standing grant, so a client
  rule demanding per-branch permission is already answered); ask about any other branch.
- **One commit per logical change.** Rewrite unmerged commits freely (amend, `--fixup` +
  autosquash, squash, reorder, split) so review fixes fold into their commit with no
  `wip`/`address review` churn. `--force-with-lease` after a rebase, never bare `--force`.
- **Title commits like a changelog line** (maintainer, 2026-10-23): after any prefix, an
  imperative verb, then the change as a visitor to the site sees it, plain English,
  sentence case, ≤ ~70 chars, e.g. `Fix …` for what was broken, `Improve …` for what got
  better, `Add …` for what's new; an optional parenthetical says how. Never the scenario
  or the mechanism (that's the body). PR titles match.
- **Merge cue (`merged` / `I merged` / `landed` / merge webhook) runs hygiene first:**
  `git fetch origin +refs/heads/main:refs/remotes/origin/main` (a bare fetch leaves a
  single-branch `origin/main` stale), cut a fresh `<agent>/<short-topic>` off
  `origin/main`, announce the switch; if unable to fetch, say the follow-up needs a synced
  checkout rather than branching off a stale `origin/main`.
- **Unshallow before history-depth queries** (`git rev-list --count`, `git log` past the
  boundary, blame): if `git rev-parse --is-shallow-repository` is `true`, run
  `git fetch --unshallow` and re-check; it exits 0 even when it deepened nothing, so if
  still `true`, say the history is truncated rather than quote a count.
- **No model identifier** — never name the coding agent's model or version (`Opus 4.8`,
  `Sonnet`, `Gemini …`, `claude-*`, `gemini-*`) in a commit, PR, comment, or pushed
  artifact; keep it to chat. Generic attribution (`Co-Authored-By: Claude` / `Gemini`,
  `Claude-Session:`, "Generated with Claude Code") is fine.

## Talking to the user

- **One question at a time** — in plain chat or the client's question tool
  (`AskUserQuestion` in Claude Code, `ask_question` in Antigravity). After asking, stop
  and wait: don't proceed on an assumed answer, pick a "recommended" option, or keep
  working on the part it affects. Never ask while the user is typing.
- **Answer a mid-turn message first**, before any further tool call, even in one sentence
  (except merge cues, whose hygiene runs first and whose announced switch is the answer).
- **Message only when the user needs to see it** (maintainer, 2026-10-15): each notifies
  their phone. Work in silence; speak up for a question/blocker, something to merge or act
  on, a merge, an autopilot decision (to review when seen, never waited on), or a change
  from the plan or their instructions (review-prompted included). Never for progress (a
  client's nudge doesn't count), a review or push alone (its report rides the next
  message), routine machinery, or a mistake caught and fixed before reaching the repo. The
  session-start `AGENTS.md` line still opens every session.
- **Keep replies short**: lead with the single most important point; ask before unloading
  more.
- **End the turn by restating any pending decision** — the last line is the question you
  are waiting on, written out (not "as asked above"), every turn until answered; the
  open-PR link goes just above it. Nothing pending, no line. A scheduled check that finds
  nothing new re-arms silently and sends no reply.

## Pull requests

- Prefer `mcp__github__*` tools where mounted (Claude Code requires them); otherwise fall
  back to `gh`. If your client exposes neither, say so rather than guess at an outcome.
- **Open the PR without being asked**, ready for review (not draft, unless asked), unless
  told "just commit / no PR yet" (holds until lifted). This file is the repo owner's
  standing request, so a client rule "open a PR only when asked" is already satisfied.
- **Update the PR title and body with the push — body first, then push** — to match the
  full branch diff against `origin/main`, and post the PR link in the next message. With
  no PR yet, push, then do this as soon as one is opened.
- **"Drive to merge"**: open the PR, wait for the automatic Codex review, address every
  comment (fix, or reply why not), and merge once CI is green and Codex's verdict for the
  current head is in.
- **Ordered work ("next", "then", "after that", "follow-up")** may open in parallel but
  merges only after every earlier session item and any PR the paragraph names has merged
  (any repo, no time cap; hold and ask if one won't finish, autopilot included; arm no
  auto-merge until then, since it can't see the order; read the list from the session's
  record, not memory).
- **List every open PR on a feature by URL, one per line** — the "View PR" chip sticks to
  the first link (anthropics/claude-code#46625).
- **End every reply with the open-PR link** (or `.../compare/main...<branch>` until one
  exists); never link a closed or merged PR, except in post-merge follow-up on it.

## Reviews

- **Codex is the automated reviewer** (not Copilot), triggered automatically; request it
  only to confirm a rebutted false positive or as *Read the Codex verdict* allows.
- **Address every comment unasked**: fix it in this PR, folded into its commit (`--fixup`;
  group same-topic small fixes), or defer a real out-of-scope one (below).
- **Judge comments on merit**, whoever wrote them: verify the claim before acting, and if
  it doesn't hold up, reply why and decline. A cited rule is a reading — check what it
  says; Codex reads the privacy rules over-strictly, quietly costing needed capability, so
  quote the rule and decline rather than narrow the code. A genuine rule-vs-need conflict
  is the maintainer's call, not yours to settle either way. Declining doesn't clear the
  required `codex` status: post the rebuttal, then poke as *Read the Codex verdict* allows
  (or let the next push do it, if the rebuttal is up first); escalate if it re-raises.
- **A second verified finding in the same mechanism is a design question**: look for the
  shape elsewhere and ask whether a different design deletes the class; say what you chose
  on the thread (a design change is the maintainer's call, autopilot included).
- **Never silently dismiss a thread**: answer (a disagreement is an answer — say why, a
  false positive in a sentence or two), then resolve once the fix is on the head or the
  point is rebutted; anything still to do stays open. Acknowledgment noise beats silence.
- **Defer a real out-of-scope finding** rather than ask to merge past it: push a `TODO.md`
  entry first, reply with that sha, and resolve (the one open-work exception); a
  threadless finding gets the entry, push and reply, only no resolve. The push re-triggers
  Codex, so poke only as *Read the Codex verdict* allows; escalate if the re-review
  re-raises it.
- **`resolve_review_thread` takes the `PRRT_*` thread ID** (`review_threads[].id` from
  `get_review_comments`; `gh api graphql` `resolveReviewThread` without the MCP tools), not
  a comment's `PRRC_*`. Push the fix, reply citing the new sha, then resolve.
- **Report each review in your next message**: commit read (say if it's no longer the
  head), finding count, one bullet per finding — review comment, top-level comment or
  review body, most blocking first: claim, location, and what you did or the maintainer's
  options. All of them, ahead of *keep replies short*; ask only the most blocking question.
- **Read the Codex verdict, don't infer it.** It reacts to the PR body (`issue_read` →
  reactions), not a thread's `Useful?` bar: `eyes` reading, `+1` clean, revoked on push, so
  a visible one belongs to the visible head; `+1` with green CI is a merge. Leave body
  reactions to Codex (the count names no author; a review names the commit it read).
  Findings arrive as review comments, top-level comments or reviews — read all three to the
  last page — and block the merge until fixed, rebutted or deferred; an acknowledgment is
  no answer. A pending `codex` status is findings to address; or a clean review with no
  reaction or an unanswered rebuttal — poke `@codex review` five minutes after it; or a
  hung review, nothing at all five minutes after the push or stuck at running (👀) ten
  minutes on — poke. A poke that hangs the same way gets a second an hour later; escalate
  only if that one hangs too, never after one (maintainer, 2026-10-22).
- **Once Codex has +1'd a head, make no unnecessary change without asking** (maintainer,
  2026-10-13): a to-do, tidy-up or extra fix waits for a yes or a follow-up PR; a rebase
  for `dirty` (or required `behind`), a red-CI fix, and drive/autopilot where in effect
  proceed unasked.
- **Skip your own echo events silently** (did *I* just post this body?, not who's the
  author).
- **Watch your own PRs by subscription + one scheduled check.** Subscribe on open
  (automatic in Claude Code, or `subscribe_pr_activity` where `claude-code-remote` exposes
  it; a client with neither, like Antigravity, relies on the scheduled check alone) for
  reviews, comments and CI failures. It misses CI success, pushes, the merge, Codex's `+1`
  and Codex never answering, so keep exactly one check armed while the PR is open
  (`send_later` in Claude Code; `schedule` with `DurationSeconds` in Antigravity, canceled
  via `manage_task` `kill`); each event and check costs a model turn. (This replaced a
  scheduled-check-only watch: the scheduler ignored its intervals, events land on time.)
  - Settle a fired check first — it may have re-armed rather than retired: update the
    survivor, replace one that didn't; end each turn with exactly one pending.
  - Compare the fire time you got to the one you asked for (4 minutes has come back as
    64); prefer a relative delay, since an absolute time from this container's clock can
    be rejected as past. Re-time it, or say the watch isn't armed.
  - Minutes while CI or the head's Codex verdict is out or after a push; longer once only
    a human is left.
  - Name the PR and say what to re-read, never a SHA.
  - **Wake PRs a merge leaves behind.** First turn after your PR merges (by hand or
    auto-merge), message every other open PR on that base that another session drives
    (its body ends with the session URL): name that PR and say only that its base now
    points at `<sha>`, whatever its state reads (mergeability may still be computing);
    name no merge and no other PR, since an older copy of these rules reads either as a
    merge cue. On receipt, fetch base and PR head by refspec, unshallowing, and test
    against the fetched base tip, not `<sha>`: `behind` if `git merge-base
    --is-ancestor <tip> <head>` exits 1, `dirty` if `git merge-tree --write-tree` (Git
    2.38+) exits 1; any other exit is a failure to report. Your own rules decide the
    rebase. Skip with no session URL or local-only messaging; don't retry a failed send
    (its own check is the fallback).
  - **Merged or closed**: hold one more short check for CI and Codex on the final head,
    without blocking on a report that may never come (early manual merge, review service
    down). Then a last reply-and-resolve pass: anything real on a merged PR goes to a
    follow-up PR (with its own watch), named on the thread, before resolving; a
    closed-unmerged PR is a stop — answer, resolve, open nothing. Only then cancel the
    watch in full (the pending check and, if subscribed, `unsubscribe_pr_activity`);
    `list_triggers` spans the account, so match this session and PR first.
- **A PR reading `dirty` — always — or `behind` where branches must be up to date needs a
  rebase and a lease-guarded force-push.** No webhook reports a base advance, so read
  `mergeable_state` at every check, PR-event wake and drive step, and act at once,
  unasked: fetch both refs by refspec, unshallow, and rebase onto the fetched
  `origin/<base>`, never the local branch. First confirm your branch has every remote head
  commit, and before pushing that the head hasn't moved since the tip you noted before
  fetching — the push flags don't reliably refuse a rewind or an unfetched or unrebased
  commit, and overwriting one loses work. If either fails, or you can't tell, stop and
  ask.

## Cost and reliability

Call out cost and reliability up front for new infrastructure (an App Engine
instance-class change, a datastore, a cache, a monitoring service) or a new external API
call: $/month vs free tier at expected traffic, failure modes, rate limits, latency, extra
points of failure, and what a visitor sees when it's down. App Engine's free tier is the
baseline, so anything moving the app off it needs saying. Say so if the impact is nil.
