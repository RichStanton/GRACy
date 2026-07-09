# Backlog

Git-tracked mirror of the live work items. The **source of truth is GitHub Issues** on
`RichStanton/GRACy` — this file is a convenience index so the backlog is visible in the repo.
Filed 2026-07-09 from `../architecture/improvement-plan.md` + `../../agent_workspace/planning/code_review.md`.

Issues: <https://github.com/RichStanton/GRACy/issues>

## Confirmed bug hotfixes — `ready-for-agent`

| # | Title | Blocked by |
|---|---|---|
| [#2](https://github.com/RichStanton/GRACy/issues/2) | BUG-1: `toPlainText` missing `()` — guard never fires (6 modules) | — |
| [#3](https://github.com/RichStanton/GRACy/issues/3) | BUG-2: `completeGenome.py` writes `firstPortion` as last portion → silent wrong genome | — |
| [#4](https://github.com/RichStanton/GRACy/issues/4) | BUG-3: `genotypingQt.py` hardcodes `16` instead of `kmerLength` | — |
| [#5](https://github.com/RichStanton/GRACy/issues/5) | BUG-4: `warnings` used before declaration in `annotationQt.py` | — |
| [#6](https://github.com/RichStanton/GRACy/issues/6) | BUG-5: hardcoded HCMV genome size `235646.0` in `readsFilteringQt.py` (×2) | — |

## Improvement plan — mechanical (`ready-for-agent`)

| # | Title | Blocked by |
|---|---|---|
| [#7](https://github.com/RichStanton/GRACy/issues/7) | Delete the dead non-Qt twins (+ `.bak`, `._*` copies) | — |
| [#8](https://github.com/RichStanton/GRACy/issues/8) | Repo hygiene — un-track Miniconda installers/junk; extend `.gitignore` | — |
| [#9](https://github.com/RichStanton/GRACy/issues/9) | Fix committed `GRACy.py` artifact + hardcoded HPC path | — |
| [#10](https://github.com/RichStanton/GRACy/issues/10) | Polish — `>null`→`/dev/null` (201×), typos, fork README | — |
| [#11](https://github.com/RichStanton/GRACy/issues/11) | End-to-end smoke test on `testDataset/` + CI (safety net) | toolchain install |

## Improvement plan — structural (`ready-for-human`, HITL)

| # | Title | Blocked by |
|---|---|---|
| [#12](https://github.com/RichStanton/GRACy/issues/12) | Command-runner module `run(tool, *args)` — path + return-code check + logging | #7 |
| [#13](https://github.com/RichStanton/GRACy/issues/13) | Alignment module `align(reads, ref) → bam` | #12 |
| [#14](https://github.com/RichStanton/GRACy/issues/14) | Extract a headless pipeline module (GUI↔pipeline seam) | #11, #12 |
| [#15](https://github.com/RichStanton/GRACy/issues/15) | Config module — keyed, validated `.conf` parsing | #14 |
| [#16](https://github.com/RichStanton/GRACy/issues/16) | `os.system` → `subprocess.run([...], shell=False)` (incremental) | #12, #11 |
| [#17](https://github.com/RichStanton/GRACy/issues/17) | Collapse the Python 2 env (Ragout on Py3) | #11 |

## Status

- **2026-07-09** — backlog filed (#2–#17). Recommended first sequence: BUG-2 (#3) → BUG-3 (#4) →
  BUG-5 (#6), then #11 (smoke test) once the toolchain is installed. See the current
  [journal entry](../journal/2026-07-09.md).
