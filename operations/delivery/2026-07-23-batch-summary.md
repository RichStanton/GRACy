# GRACy — fixes delivered 2026-07-23

**For:** the maintainer / anyone testing this build.
**State:** all changes below are merged to `master` (@ `ea75bb3`). Test suite: **14/14 passing.**

Six issues were delivered across five pull requests (#24–#28), now closed. These are **bug fixes and
repo cleanup only — no changes to the scientific/analytical logic**. Pipeline *results* should be
identical to before; the fixes make the app fail *gracefully* instead of crashing, and make the repo
clean. Test pointers are below — none require a full scientific validation run.

## The changes, and how to test each

### #23 (BUG-6) — blank-field warnings no longer crash the app
- **What:** three screens (Assembly, Annotation, SNP calling) were missing an internal import, so if you
  started them with a required field empty, the app **crashed to the terminal** instead of warning you.
- **Test:** open **Assembly**, then **Annotation**, then **SNP calling**. In each, leave a required file
  field blank and click run.
  **Expect:** a small popup dialog telling you what's missing.
  **Before the fix:** it would have thrown an error in the console and done nothing.

### #10 — no more stray `null` files; typos fixed
- **What:** 124 shell commands wrote output to a file literally named `null` instead of the system
  `/dev/null` sink. That littered your working directory with junk files. Also fixed log/UI typos and a
  broken upstream link in the README.
- **Test:** run any pipeline stage inside an empty scratch folder.
  **Expect:** no file named `null` appears in that folder afterward. On-screen and log messages read
  cleanly.

### #7 + #8 — repo cleanup; installer slimmed
- **What:** removed ~488,000 lines of committed junk — two bundled Miniconda installers, dead duplicate
  scripts, macOS `.DS_Store` / `._*` files, and `.bak` files. `install.sh` now **downloads Miniconda on
  demand** rather than shipping it. (The live `webin-cli` submission tool was deliberately **kept**.)
- **Test:** on a **fresh clone**, run `bash install.sh`.
  **Expect:** it downloads Miniconda and completes; the app launches and a pipeline stage runs as before.

### #9 — launcher no longer carries a foreign machine's path
- **What:** the generated `GRACy.py` launcher had been committed with a **hardcoded path from another
  person's machine**, which could break launching. It's now generated locally and no longer tracked.
- **Test:** fresh clone → `bash install.sh`.
  **Expect:** `GRACy.py` is regenerated pointing at *your* local Python, and `git status` stays clean
  (it won't prompt you to commit it).

### #3 (BUG-2) — low-impact correctness tidy
- **What:** `completeGenome.py` now writes the correct sequence into its `>lastPortion` record.
- **Impact:** **Low** — this file is a dead duplicate; the live pipeline uses `completeGenome2.py`,
  which was never affected.
- **Test:** no live-pipeline test needed. If anyone runs `completeGenome.py` directly, its output FASTA
  now contains the right last-portion sequence.

## Regression safety net
The automated test suite grew from 10 to **14 tests**, all passing. The BUG-6 and BUG-2 fixes each ship
with a test that fails if the bug is reintroduced. Run them anytime with:

```
src/conda/bin/python -m unittest discover -s tests
```