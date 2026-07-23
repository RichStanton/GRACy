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

## Bugs from testing — `ready-for-agent`

| # | Title | Blocked by |
|---|---|---|
| [#23](https://github.com/RichStanton/GRACy/issues/23) | BUG-6: `QMessageBox` never imported in assembly/annotation/snpCalling — input guards raise NameError to terminal (latent bug unmasked by #2) | — |

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

- **2026-07-09** — backlog filed (#2–#17); toolchain installed.
  - **#2 (BUG-1)** — fixed + regression tests; **merged** ([PR #18](https://github.com/RichStanton/GRACy/pull/18)).
  - **#4 (BUG-3)** — fixed test-first + regression tests; **merged** ([PR #19](https://github.com/RichStanton/GRACy/pull/19)).
  - **#6 (BUG-5)** — fixed test-first + regression tests; **merged** ([PR #20](https://github.com/RichStanton/GRACy/pull/20)).
  - **#5 (BUG-4)** — fixed test-first + AST regression test; **merged** ([PR #21](https://github.com/RichStanton/GRACy/pull/21)).
  - **#3 (BUG-2)** — reclassified Critical → **Low** (writes to dead code; no wrong genome). Deprioritised as tidy-up.
  - **Next:** all confirmed bug hotfixes are **merged** (`master` @ `4713ba2`; 10 tests green). Block 1
    of the improvement plan resumes at **#11** (smoke test), which unlocks end-to-end verification for
    the structural items (#12–#17).
  - Progress detail in the [journal](../journal/2026-07-09.md).

- **2026-07-22** — AFK batch: five PRs opened from `master`, all left **open for review** (no self-merge).
  Held #11 (smoke test — golden output needs human validation).
  - **#23 (BUG-6)** — `QMessageBox` never imported in assembly/annotation/snpCalling; input guards
    raised `NameError` to the terminal instead of a dialog (unmasked by the #2 fix). Fixed test-first.
    [PR #24](https://github.com/RichStanton/GRACy/pull/24).
  - **#3 (BUG-2)** — `>lastPortion` record now written from `lastPortion` (dead-code twin; live pipeline
    uses `completeGenome2.py`, unaffected). Test-first. [PR #25](https://github.com/RichStanton/GRACy/pull/25).
  - **#9** — gitignore + untrack the generated `GRACy.py` launcher (stale foreign path). Verified fresh
    clone + install regenerates it. [PR #26](https://github.com/RichStanton/GRACy/pull/26).
  - **#7 + #8** — repo hygiene: removed 70 files (dead twins, `._*`/`.DS_Store`/`.bak`, Miniconda
    installers); install.sh now downloads Miniconda on demand. **Kept `webin-cli-4.2.0.jar`** (live dep).
    [PR #27](https://github.com/RichStanton/GRACy/pull/27).
  - **#10** — `>null`→`/dev/null` (124× in live files), log/UI typos, fork README upstream link.
    [PR #28](https://github.com/RichStanton/GRACy/pull/28). ⚠️ Overlaps pre-existing
    [PR #22](https://github.com/RichStanton/GRACy/pull/22) (`nightcityblade`) which also closes #10 and
    conflicts with #27 — maintainer to pick one.
  - **Ordering note:** #27 deletes files that #22 edits; #28 was scoped to live files to compose with #27.

- **2026-07-23** — AFK batch **merged** (squash) by user request: PRs #24, #25, #26, #27, #28 all landed;
  issues #23, #3, #9, #8, #7, #10 auto-closed. `master` @ `7bd5e80`; **14 tests green**. #27 needed a
  one-line `.gitignore` conflict resolved (kept both the #7/#8 junk patterns and the #9 `GRACy.py`
  entry). Housekeeping: gitignored + removed stale install byproducts (`installation.log`, `condaList`,
  `src/installation.log`).
  - **`ready-for-agent` now clear except #11** (smoke test — still held; needs a maintainer-blessed
    golden output). Everything after is `ready-for-human` (#12–#17).
  - ⚠️ **Community PR #22** (`nightcityblade`, also closed #10) is now redundant/conflicting since #28
    landed — maintainer should close it.
