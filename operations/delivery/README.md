# Delivery method

How work flows for GRACy.

- **Tracker:** GitHub Issues on `RichStanton/GRACy` (this fork — see `docs/agents/issue-tracker.md`).
- **Triage labels:** `needs-triage` · `needs-info` · `ready-for-agent` · `ready-for-human` · `wontfix`
  (see `docs/agents/triage-labels.md`).
- **One issue → one PR.** Claude builds and verifies; you own decisions, forks, and merges.
- **Decisions that gate work or would surprise a future reader → an ADR** in `operations/decisions/`.
- Pipeline: `grill-me`/`grill-with-docs` (align) → `to-prd` (spec issue) → `to-issues` (vertical
  slices) → `triage` (gate to `ready-for-agent`) → `tdd`/`diagnose` (execution).
