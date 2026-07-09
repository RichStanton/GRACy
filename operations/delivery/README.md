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

## Other rules

- **Decisions that gate work or would surprise a future reader → an ADR** in `operations/decisions/`.
- **Backlog:** current work items are issues #2–#17; see [`backlog.md`](./backlog.md) for the
  git-tracked index.
