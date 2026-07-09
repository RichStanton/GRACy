# Phase 3 — Prioritised Work Plan

**Owner:** IK
**Status:** Draft
**Date:** 2026-05-20
**Inputs:** `code_review.md`, `architecture_review.md`, `TASKS.md`
**Method:** effort × value scoring; quality-tooling items weighted up one tier

---

## Scoring method

Each item is rated on two axes:

| Axis | 1 | 2 | 3 |
|------|---|---|---|
| **Effort** | Minutes–hours (1–5 lines or one command) | Hours–days (one module, systematic) | Days–weeks (cross-codebase refactor) |
| **Value** | Critical correctness / prevents wrong science | Reliability, security, or enabling future work | Code hygiene, style |

Priority = high value + low effort. Quality-tooling items (linting, pre-commit, test harness) receive a **+1 value bonus** because they multiply the benefit of every future change.

---

## Tier 1 — Fix now (minutes each, critical correctness)

These are confirmed bugs that produce wrong results or crash silently. Each is a 1–2 line change. Do these before anything else.

| Task | File(s) | Why first |
|------|---------|-----------|
| **TASK-021** — Add `()` to `toPlainText` in all 5 Qt modules | `assemblyQt.py:143`, `genotypingQt.py:194`, `snpCallingQt.py:273`, `dbsubmissionQt.py:319`, `readsFilteringQt.py:302` | Without this the "no files selected" guard never fires. Users who click Run without selecting files get a crash with no message. Five 1-line fixes. |
| **TASK-022** — `firstPortion` → `lastPortion` in `completeGenome.py:105` | `src/scripts/assembly/utils/completeGenome.py:105` | Copy-paste bug silently writes the first genome segment twice. Every assembly through this function produces a wrong FASTA. 1 line. |
| **TASK-023** — Replace hardcoded `16` with `kmerLength` in `genotypingQt.py:511` | `src/scripts/genotyping/genotypingQt.py:511` | Hardcoded k-mer length means the second loop always uses 16-mers regardless of the user's setting. Silent wrong counts. 1 line. |

**Combined effort:** ~30 minutes. **Combined impact:** prevents incorrect science output on every run.

---

## Tier 2 — Install quality tooling (hours, pays dividends forever)

These items are weighted up because they prevent new issues from accumulating. Do this while Tier 1 fixes are fresh — the tools then give you a clean baseline going forward.

### 2a — Add Ruff + pyproject.toml (TASK-027)

**Effort:** ~1 hour.
**Value:** Ruff found 436 violations. Once the config is committed, every future edit gets instant feedback. The E712/E713 comparison fixes (210 instances) are *auto-fixable in one command* — 210 issues cleared for ~5 minutes of work.

**Steps:**
1. `pip install --user ruff`
2. Create `pyproject.toml` with the config from `code_review.md` (target py38, select E/F/W, ignore E501).
3. Run `ruff check --fix src/` — auto-fixes the 210 comparison anti-patterns.
4. Run `ruff check src/` to see the remaining 226 violations as a tracked baseline.
5. Commit `pyproject.toml`. Violations are now visible in the editor and reviewable.

**Why before the subprocess migration:** once Ruff is in place, new `subprocess` code you write is checked automatically.

### 2b — Add pre-commit hook (optional — do if RS is committing)

**Effort:** 30 minutes.
**Value:** Ruff runs automatically on every commit. The `.pre-commit-config.yaml` from `code_review.md` is ready to paste in.

**When to do:** as soon as RS is back in active development, or immediately if you want the discipline for solo work.

### 2c — Fix `.gitignore` and delete AppleDouble files (TASK-016 + TASK-017)

**Effort:** 15 minutes.
**Value:** Both linters silently skip the `._*.py` files (binary). One `git rm` and two lines in `.gitignore` clears the noise permanently.

---

## Tier 3 — Small high-value cleanup (hours total, no structural risk)

These are isolated, low-risk fixes with disproportionate impact on reliability or correctness. Do these in any order within the tier.

| Task | Effort | Why now |
|------|--------|---------|
| **TASK-024** — Remove `sys.stdin.read(1)` debug pauses in `dbsubmissionQt.py:521,546` | 5 min | These lines block the GUI thread — the window freezes waiting for a keypress. Delete 2 lines. |
| **TASK-026** — Remove debug `print()` statements from `polyAn.py` and `dbsubmissionQt.py` | 30 min | ~15 print statements pollute stdout in production. All confirmed debug statements. |
| **TASK-025** — Move `makeblastdb` call out of loop in `lncRNA_annotation.py` | 30 min | Currently rebuilds the BLAST DB once per lncRNA candidate. Move 1 block before the loop — significant unnecessary slowdown on any genome with many lncRNA candidates. |
| **TASK-028** — Fix deprecated `Seq.reverse_complement()` in `varscanFilter.py` | 30 min | Biopython API changed; will fail or warn on any recent install. |
| **Delete `assembly.py` + `assemblyQt.bak`** (TASK-033, confirmed by arch review) | 30 min | `assembly.py` is confirmed dead code: not called anywhere, would fail at runtime (references two utils that don't exist — `retrieveNodes.py`, `getSequenceFromFasta.py`). `assemblyQt.bak` is a committed backup file. Both are noise. The architecture review confirms no investigation is needed — delete confidently. This removes ~1,300 lines of misleading dead code. |
| **TASK-018** — Remove commented-out dead code throughout | 1–2 hours | `assemblyQt.py` alone has 10+ blocks of commented `os.system()` calls. Dead code raises cognitive load on every read-through. No risk — it's already unreachable. |

**Architecture note on `assembly.py`:** the earlier task spec (TASK-033) suggested an investigation before deleting. The architecture review resolves this — the file is definitively dead. The missing utilities it depends on simply do not exist; the active variant-caller path diverged at `bcftools consensus` which only `assemblyQt.py` has. Delete without hesitation.

---

## Tier 4 — Subprocess migration (do module by module — TASK-010, CC-1, CC-2)

**Effort:** 1–2 days total across sessions; approach one module per session.
**Value:** The single highest-impact structural change. Fixes:
- 579 definite shell injection sites (spaces in paths break every run; shell metacharacters in passwords expose credentials)
- Silent pipeline failures (when a tool crashes the pipeline currently continues and produces garbage)
- The `dbsubmissionQt.py` credentials security issue (passwords passed raw through shell)

**Why not Tier 2:** The scale (916 instances across every module) requires care. Rushing it risks introducing new bugs. Ruff and Tier 3 cleanup first puts you in a better position to work on each file cleanly.

### Tier 4a — Make Class-B utility scripts importable (new — from architecture review)

**Effort:** ~30 minutes each, 3 scripts total.
**Why first:** The architecture review identifies `scaffold_builder.py`, `revComp.py`, and `varscanFilter.py` as "quick wins" — these three already have function structure and need only a `__main__` guard or a `main()` wrapper. Making them importable is a stepping-stone: once they are, the assembly pipeline can call them in-process rather than via `os.system()`, which eliminates some of the 916 injection sites before you even touch the main module files.

**Steps for each:**
- `scaffold_builder.py` — move module-level execution block into `if __name__ == "__main__":`. ~30 min.
- `revComp.py` — 4-line script; wrap logic in `def rev_comp(seq): ...` + `__main__` guard. ~15 min.
- `varscanFilter.py` — uses argparse; wrap in `main()` function + `__main__` guard. ~30 min.

These are also needed for TASK-028 (`varscanFilter.py`) so both fixes can land in the same commit.

### Tier 4b — Full subprocess migration, per module

**Recommended order** (least critical path to most):

1. `dbsubmissionQt.py` first — credentials in shell commands is the most acute security issue. Also where Tier 3 debug pauses and prints land, making this a natural continuation of that work.
2. `lncRNA_annotation.py` and other utility scripts — smaller files, lower blast radius.
3. `readsFilteringQt.py` — contains the wildcard `rm` that can delete user files.
4. `snpCallingQt.py`
5. `genotypingQt.py`
6. `annotationQt.py`
7. `assemblyQt.py` last — largest and most complex.

**Pattern for each module:**
```python
# Before
os.system(installationDirectory + "src/conda/bin/spades.py -1 " + read1 + " -2 " + read2 + " ...")

# After
import subprocess
result = subprocess.run(
    [installationDirectory + "src/conda/bin/spades.py", "-1", read1, "-2", read2, ...],
    check=False
)
if result.returncode != 0:
    self.logArea.append("SPAdes failed — see output above")
    return
```

Use `check=False` with explicit `returncode` handling rather than `check=True` (which raises), so you can give the user a readable message before aborting.

---

## Tier 5 — File context managers (CC-4, 1–2 hours)

**Effort:** Mechanical but systematic — find every bare `open()`, wrap with `with`.
**Value:** Prevents file descriptor leaks in batch mode. On a 50-sample batch run the current code opens 4+ files per sample with no guaranteed close. Most OS will recover, but it can cause `OSError: too many open files` on large batches.

**Do alongside Tier 4** — once you are already touching a file for subprocess migration, fix its context managers in the same pass. No need for a separate sweep.

---

## Tier 6 — Document inter-module contracts (prerequisite gate for Tier 7)

**Effort:** ~half a day.
**Value:** The architecture review is explicit: *formalise before any module-level API change.* All six contracts are currently implicit — hardcoded directory names (`1_cleanReads/`, `2_spadesAssembly/`, etc.), magic filename suffixes (`_nh`, `_tr`, `_dd`, `_hq`), and hardcoded relative paths like `../2_spadesAssembly/scaffolds.fasta`. If you refactor a module's output path or filename without documenting the contract first, the downstream module silently breaks.

**This is a gate, not optional.** Do this before Tier 7 (God-method extraction), not after. Document using the compound-engineering skill covering:
- Input filename patterns and directory layout per module
- Output filename patterns and what is guaranteed to exist after a successful run
- The Reads Filtering → Assembly contract specifically (most fragile: Assembly hardcodes the relative path `./1_cleanReads/qualityFiltered_1.fq`)

**This is not implementation work** — it is reading the current code and writing down what it already expects. The payoff is that Tier 7 refactoring can be done against a spec, not by reverse-engineering the pipeline as you go.

---

## Tier 7 — Extract God methods + build test harness (TASK-011, TASK-015, TASK-030)

**Effort:** 2–5 days per module; assembly is the largest.
**Value:** This is the prerequisite to unit testing. Nothing can be tested in isolation until the pipeline logic is separate from the GUI class.

**Architecture review finding:** the callback pattern is confirmed feasible. There are **no** `processEvents()` or `QEventLoop` calls inside `performAssembly()` — the pipeline does not depend on the Qt event loop to make progress. The extraction pattern is: replace `self.logArea.append/repaint()` calls with a `progress_callback(message)` argument, and replace inline widget reads (`self.memoryCombo.currentText()`) with function parameters.

**Critical: `os.chdir()` must be resolved in the same pass.** The architecture review confirms 13 `os.chdir()` calls in `assemblyQt.py`. These are safe today (each module runs as a separate OS process), but if extraction consolidates modules into one process, shared working directory state would corrupt inter-step behaviour. The fix is: replace every `os.chdir(subdir)` + relative path combination with an absolute path constructed from `projectDirectory / subdir / filename`. Do not defer this — attempting to extract the function without fixing `os.chdir()` would produce a function that is only safe to call once and breaks on reuse.

**Recommended extraction sequence** (smallest to largest):
1. `snpCallingQt.py` (229-line method — lowest risk, best learning exercise).
2. `genotypingQt.py` (451 lines).
3. `readsFilteringQt.py` (577 lines).
4. `annotationQt.py` (1,200 lines).
5. `assemblyQt.py` (1,121 lines) — last; needs the `os.chdir()` fix in the same pass.

**Test harness (TASK-015)** becomes viable as soon as one module is extracted. The assembly pipeline is the right first target: BUG-2 (wrong genome sequence written silently) is exactly the class of error a regression test would catch. Build the test harness for assembly immediately after extracting `assemblyQt.py`.

**Class-C utility scripts (TASK-032):** 15 scripts need function extraction. The architecture review correctly groups these with TASK-011 — address each script as part of the module refactor that calls it, rather than as a separate sweep. This spreads the work across sessions and keeps each utility change in context.

---

## Tier 8 — Defer (low value-to-effort ratio right now)

| Task | Why defer |
|------|-----------|
| **TASK-013** — Collapse Python 2 conda environment | Needs Ragout Python 3 compatibility verified. Low urgency while assembly pipeline is the focus. |
| **TASK-014** — Remove Miniconda binaries from repo | Correct but no user-visible impact. |
| **CC-7** — Type annotations + docstrings | Very high effort (~6,000 lines). Begin incrementally after Tier 7: annotate extracted functions as you write them. |
| **TASK-019** — Fix 4 typos in log messages | Trivial; batch into another PR. |
| **TASK-020** — Write proper README | Do when install process is more stable (post-TASK-013). |

---

## What changed versus the code-review-only plan

| Change | Source | Effect on ordering |
|--------|--------|-------------------|
| `assembly.py` + `assemblyQt.bak` confirmed deletable without investigation | Arch review Q5 | Moves from "defer/investigate" to Tier 3 |
| Class-B scripts (`scaffold_builder.py` etc.) are natural first subprocess targets | Arch review Q3 | New Tier 4a step before full subprocess migration |
| Inter-module contracts must be documented before API-changing refactors | Arch review Q2 | New Tier 6 gate before God-method extraction |
| `os.chdir()` must be fixed in same pass as `performAssembly()` extraction | Arch review Q1+Q4 | Adds scope to Tier 7 assembly step — cannot be split |
| Callback extraction confirmed feasible (no `processEvents()` in pipeline) | Arch review Q1 | Tier 7 is less risky; no "full rewrite" risk |

---

## Summary table

| Tier | Tasks | Effort | Value driver |
|------|-------|--------|--------------|
| 1 | TASK-021, 022, 023 | ~30 min | Correct science output — 1-liners |
| 2 | TASK-027 + Ruff auto-fix, pre-commit, .gitignore | ~2 hrs | Quality infrastructure, multiplies all future work |
| 3 | TASK-024, 025, 026, 028, 018; delete `assembly.py` + bak | ~3 hrs | Reliability, performance, dead-code removal |
| 4a | Make Class-B utils importable (TASK-031) | ~1.5 hrs | Stepping-stone for in-process calls; enables Tier 4b |
| 4b | subprocess migration, per module (TASK-010) | ~2 days | Security + silent failure prevention |
| 5 | Context managers (CC-4) — alongside Tier 4b | ~2 hrs | Resource safety in batch mode |
| 6 | Document inter-module contracts (TASK-029) | ~half day | Gate: must precede API-changing refactors |
| 7 | Extract God methods + fix os.chdir + test harness (TASK-011, 030, 015) | ~2 weeks | Testability, headless future, long-term maintainability |
| 8 | TASK-013, 014, CC-7, 019, 020 | Varies | Defer — low urgency or blocked on earlier tiers |

---

## Recommended next session

1. Fix all three Tier 1 bugs (~30 min) → commit as `hotfix: correct toPlainText, lastPortion, kmerLength bugs`.
2. Install Ruff, create `pyproject.toml`, run `ruff --fix` on E712/E713 (~1 hour) → commit as `tooling: add Ruff baseline, auto-fix 210 comparison anti-patterns`.
3. Work through Tier 3 cleanup (~3 hours) → commit as `cleanup: remove debug pauses/prints, fix makeblastdb loop, Biopython deprecation, delete dead assembly.py and bak`.

This sequence delivers the highest value per hour and leaves the codebase in a significantly safer, cleaner state before the subprocess migration begins.
