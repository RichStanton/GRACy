# Delivery method

How change is delivered for GRACy. `CLAUDE.md` summarises this in a few lines; the detail lives here.

## The unit of work

- **Work = a GitHub issue** on `RichStanton/GRACy` (this fork — see `docs/agents/issue-tracker.md`).
  Always scope `gh` with `--repo RichStanton/GRACy` (this clone also has an `upstream` remote).
- **One issue → one PR.** Claude builds and verifies on a branch; **you own decisions, forks, and
  merges.** Only housekeeping (repo consolidation, docs) goes straight to `master`.
- **Triage labels:** `needs-triage` · `needs-info` · `ready-for-agent` · `ready-for-human` · `wontfix`
  (see `docs/agents/triage-labels.md`).

## The pipeline

Each stage is a skill; run them in order. Earlier stages can be skipped when the work is already
well-specified (e.g. a confirmed bug can go straight to `tdd`).

1. **`grill-me` / `grill-with-docs`** — align on what and why.
2. **`to-prd`** — turn the aligned idea into a spec issue.
3. **`to-issues`** — break the spec into independently-grabbable, vertical-slice issues.
4. **`triage`** — gate each issue to `ready-for-agent` (fully specified, AFK-ready) or `ready-for-human`.
5. **`tdd` / `diagnose`** — execution. `diagnose` to investigate; **`tdd` to build or fix.**

## Execution is test-first (`/tdd`)

Changes are delivered **red → green → refactor — not fix-first-test-after**:

1. **Plan** — agree the behaviour(s) to test with the maintainer *before* writing code.
2. **RED** — write ONE failing test that captures the behaviour (or reproduces the bug).
3. **GREEN** — minimal code to make it pass.
4. **Refactor** — only once green; re-run tests after each step.

Rules from the `tdd` skill: one test → one change at a time; test **behaviour through public
interfaces**, not implementation details; **never write all tests up front**; every change **ships
with its committed test**.

Tests live in `tests/` (stdlib `unittest`, no extra deps):

```bash
src/conda/bin/python -m unittest discover -s tests -v
```

A pipeline-level end-to-end **smoke test** (on `testDataset/`, with a golden output + CI) is tracked
as issue #11 — the safety net that makes the structural changes verifiable end to end.

## Autonomous (AFK) execution

When Claude works unattended, autonomy is bounded by the triage-label gate:

- **Scope ceiling = the `ready-for-human` gate.** `ready-for-agent` issues are fair game AFK;
  `ready-for-human` items (the structural work, #12+) are **never started** without the maintainer,
  even when they sit next in the dependency order.
- **Confirm the ceiling before a batch** — agree which issues are in scope up front.
- **Packaging:** each **bug fix is its own PR** (it ships with its committed test); pure
  **housekeeping issues are grouped** into one or two PRs to keep review load down.
- **No self-merge.** Claude opens PRs and leaves them open; **the maintainer reviews and merges.**
  A one-off "merge this" is a per-PR authorisation, not standing permission.
- **Judgement calls go in the PR body.** If a fix turns out deeper than the issue described, or a
  changed variable is dead/unused, say so in the PR so the reviewer can weigh it.

## Tooling

- **`gh` is authenticated** for this clone via `~/.config/gh/hosts.yml` (token scopes `repo`,
  `project`; it lacks `read:org`, so `gh auth login` is bypassed by writing the config directly).
  Always pass `-R RichStanton/GRACy` — default-repo resolution is ambiguous with `upstream` present.
- **Pushes go through Claude's Linux `git`**, not the user's terminal (which authenticates as
  `ikeddie`, no write access). See the journal's push-auth note.
- **Run tests with the bundled interpreter**, headless: `QT_QPA_PLATFORM=offscreen
  src/conda/bin/python -m unittest discover -s tests`.

## Other rules

- **Decisions that gate work or would surprise a future reader → an ADR** in `operations/decisions/`.
- **Backlog:** current work items are issues #2–#17; see [`backlog.md`](./backlog.md) for the
  git-tracked index.
