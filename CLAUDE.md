# CLAUDE.md

Operating guide for Claude Code in this repo. High-signal — it loads every session. It says **how we
work** and **where things live**; depth lives in `operations/` (don't restate it here).

## What this is

**GRACy** (Genome Research Assistant for CytomegaloVirus) — a desktop bioinformatics pipeline app for
end-to-end HCMV genome analysis. Wraps ~25 CLI bioinformatics tools in a Tkinter/PyQt5 GUI, targeting
Linux HPC environments and wet-lab scientists. This clone is a fork of
[salvocamiolo/GRACy](https://github.com/salvocamiolo/GRACy) (`upstream` remote) with bugfixes/updates;
`origin` is `RichStanton/GRACy`, where issues and PRs for this fork live.

## Where things live (the map)

`operations/` holds durable knowledge — read from it and write to it. Start at `operations/README.md`.

| Path | What it is |
|---|---|
| `operations/architecture/ARCHITECTURE.md` | Current understanding of the codebase, pipeline stages, tool deps. |
| `operations/delivery/README.md` | How work flows — tracker, labels, PR/merge method. |
| `operations/delivery/backlog.md` | Git-tracked index of the live work items (GitHub issues #2–#17). |
| `operations/journal/` | Dated progress log — read the latest to see where things stand. |
| `operations/decisions/` | ADRs, append-only. |
| `operations/archive/` | Historical notes, not maintained (original code review). |
| `src/` | Application code — Tkinter launcher, PyQt5 module GUIs, per-stage scripts. |
| `data/` | Reference genome, example configs. |
| `docs/agents/` | Agent-skill docs managed by `setup-matt-pocock-skills` — leave in place. |

## How we work

- **Work = a GitHub issue** on `RichStanton/GRACy` (`gh`, always with `--repo RichStanton/GRACy` —
  this clone has an `upstream` remote too). Pipeline: `grill-me`/`grill-with-docs` (align) → `to-prd`
  (spec issue) → `to-issues` (vertical slices) → `triage` (gate to `ready-for-agent`) → `tdd`/`diagnose`
  (execution).
- **Decisions that gate work or would surprise a future reader → an ADR** in `operations/decisions/`.
- **One fact, one home — link, don't restate.** This file and `operations/` prose point at facts; they
  don't duplicate them.

## Local dev

`install.sh` prepends a shebang to `GRACy.py` pointing at `./src/conda/bin/python`, then bootstraps a
local **Miniconda3** env under `src/conda/` (installing it if absent) and layers in the bioinformatics
toolchain (pillow, numpy, then the CLI tools GRACy shells out to via `os.system()` — bowtie2, samtools,
SPAdes, etc.). Linux/HPC only — no Windows/macOS support despite partial `sys.platform` checks. Run
`bash install.sh` from the repo root once; re-run is safe (skips Miniconda if `./src/conda/bin/conda`
already exists). `testDataset/` has sample reads for a smoke run through the pipeline.

## Agent skills

### Issue tracker

GitHub Issues on `RichStanton/GRACy` (this fork). See `docs/agents/issue-tracker.md`.

### Triage labels

Canonical 5-state vocabulary, mapped 1:1 to labels on this repo. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context — architecture/decisions live under `operations/`, not `docs/adr/`/`CONTEXT.md`. See
`docs/agents/domain.md`.
