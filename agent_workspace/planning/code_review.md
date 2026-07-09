# Phase 2 — Code Review

**Owner:** IK
**Status:** Complete
**Date:** 2026-05-20
**Baseline:** `archive/code_analysis/ARCHITECTURE.md` and `archive/code_analysis/initial_review.md`
**Tools run:** Ruff 0.15.13, Bandit 1.9.4

---

## Executive Summary

GRACy was reviewed across all Python source files (~7,000 lines across 20+ files) using automated static analysis (Ruff + Bandit) and manual inspection. The codebase presents **pervasive, systemic quality issues** rather than isolated bugs. The same anti-patterns recur in every module without exception.

| Category | Count | Severity |
|----------|-------|----------|
| Bandit security issues (total) | **916** | High |
| — Shell injection risk (B605, definite) | 579 | Critical |
| — Partial-path execution (B607) | 167 | High |
| Ruff style/correctness violations | **436** | Mixed |
| — Undefined names (F821) | 68 | High |
| — Unused variables (F841) | 42 | Medium |
| — Unused imports (F401) | 40 | Low |
| — Comparison anti-patterns (E712/E713) | 210 | Medium |
| Confirmed logic bugs (silent incorrect behaviour) | **5** | Critical/High |
| Files with no exception handling | **all** | High |
| Files with no type annotations | **all** | Medium |
| Files with no docstrings on public functions | **all** | Low |

**Overall risk level: HIGH.** Silent failures, shell injection, and confirmed correctness bugs mean the pipeline can produce wrong results or crash without informing the user. None of these issues are theoretical — they affect every run.

Note: 13 `._*.py` AppleDouble files (macOS resource fork artefacts) were skipped by both tools — they contain binary data, not Python. These should be deleted (see TASK-017).

---

## Cross-Cutting Findings

These patterns are present in every module. They are documented once here and not repeated per-module.

---

### CC-1 — `os.system()` with no return code checking (Critical)

**All modules.** Every external tool invocation uses `os.system()` and discards the return code. Bandit found **916 instances** across the codebase. When a tool fails (missing input, OOM, tool crash), the pipeline continues silently as if it succeeded. The next step then fails on a missing file or produces garbage output — with no indication of where things went wrong.

```python
# Typical pattern throughout the codebase — return code discarded
os.system(installationDirectory + "src/conda/bin/spades.py -1 " + read1 + " -2 " + read2 + " ...")
os.system("mv " + projectName + "_hq_1.fastq ./1_cleanReads/qualityFiltered_1.fq")
```

**Fix:** Replace with `subprocess.run()` and check `returncode`. See TASK-010.

---

### CC-2 — Shell injection via string concatenation (Critical)

**All modules.** User-supplied values (file paths, project names, thread counts, combo box selections) are concatenated directly into shell command strings passed to `os.system()`. Any value containing shell metacharacters (spaces, semicolons, backticks, `$()`, `&`, `|`) will be interpreted by the shell.

Bandit flagged **579 definite injection sites** (B605: `Starting a process with a shell, possible injection detected`). Even if intentional malicious exploitation is unlikely in this context, accidental breakage from file paths with spaces is a near-certainty for any user whose project name or path contains a space.

```python
# readsFilteringQt.py — user path from file dialog, unquoted
os.system("cp " + dataset[0] + " tempReads_140875_1.fastq")

# genotypingQt.py — output folder from user text entry
os.system("mkdir " + self.outputFolderEntry.text())

# assemblyQt.py — project name from config file
os.system("mkdir -p " + projectName)
os.system("mv " + projectName + "_hq_1.fastq ...")
```

**Fix:** Use `subprocess.run([...], shell=False)` with arguments as a list. For any residual shell calls, wrap paths with `shlex.quote()`. See TASK-010.

---

### CC-3 — All pipeline logic in `__init__` / single God method (High)

**All modules.** Every `*Qt.py` file puts its entire pipeline — hundreds to over a thousand lines — inside a single method called from the GUI button. This makes it impossible to:
- Call any pipeline step headlessly (for testing or automation)
- Reuse a step in a different context
- Unit test individual steps
- Understand or review the logic without reading the entire method

| Module | Method | Lines |
|--------|--------|-------|
| `annotationQt.py` | `runAnnotation()` | ~1,200 |
| `assemblyQt.py` | `performAssembly()` | ~1,120 |
| `assembly.py` | `performAssembly()` | ~953 |
| `readsFilteringQt.py` | `runTool()` | ~577 |
| `genotypingQt.py` | `runGenotyping()` | ~451 |
| `snpCallingQt.py` | `runTool()` | ~229 |

**Fix:** Extract pipeline logic into standalone functions outside the GUI class (see TASK-011).

---

### CC-4 — No file context managers (High)

**All modules.** Files are opened with bare `open()` calls and are never guaranteed to close, especially on exception. On a long multi-sample batch run, this can exhaust the file descriptor limit.

```python
# annotationQt.py — four files opened, no with-statement, no close guarantee
gffFile = open(suffixName + "_annotation.gff", "w")
warnFile = open(suffixName + "_annotationWarnings.txt", "w")
cdsFile  = open(suffixName + "_cds.fasta", "w")
protFile = open(suffixName + "_proteins.fasta", "w")

# assembly.py
confFile = open(cFile)   # line 159 — no context manager
```

**Fix:** Replace every `open()` with `with open(...) as f:`.

---

### CC-5 — No exception handling (High)

**All modules.** There are no `try/except` blocks around file I/O, subprocess calls, or data parsing. Any unexpected input (a truncated FASTQ, an empty BLAST result, a missing config field) raises an unhandled exception, crashing the GUI with a Python traceback rather than a user-readable error message.

---

### CC-6 — Comparison anti-patterns (Medium)

Ruff flagged **210 instances** of two related patterns:

**E712 (99 instances):** Using `==` to compare with `True`, `False`, or `None`:
```python
if os.path.isfile(projectFile) == True:    # dbsubmissionQt.py:205
if foundRecord == 0:                        # should be `if not foundRecord:`
```

**E713 (111 instances):** `not x in y` instead of `x not in y`:
```python
if not sampleName in self.experimentAccession:  # dbsubmissionQt.py:424
```

These are not bugs but make conditions harder to read and fail `not in` short-circuit evaluation.

---

### CC-7 — No type annotations or docstrings (Medium/Low)

Zero type annotations and zero docstrings across the entire codebase. All public functions take unnamed positional arguments with no indication of expected types or purpose. This makes the code significantly harder for new contributors to understand and prevents any benefit from mypy or IDE type inference.

---

### CC-8 — Python 2/3 compatibility shims still present (Low)

Several files contain `# -*- coding: utf-8 -*-` headers and `print` statement guards indicating the original code targeted Python 2. The `exit()` built-in (Python 2 style) is used in multiple utility scripts instead of `sys.exit()`. The Python 2 conda environment (`src/conda2/`) remains installed solely for Ragout, which now supports Python 3 (see TASK-013).

---

## Confirmed Bugs

These are correctness errors — not style issues. They cause incorrect or misleading behaviour at runtime.

---

### BUG-1 — `toPlainText` missing `()` — five modules (Critical)

**Files:** `assemblyQt.py:143`, `assembly.py:194`, `genotypingQt.py:194`, `snpCallingQt.py:273`, `dbsubmissionQt.py:319`, `readsFilteringQt.py:302`

The guard that checks whether the user has selected files compares a **method object** to an empty string. This always evaluates to `False`, so the check never triggers. A user who clicks Run without selecting files will not get a warning — the pipeline will proceed and immediately crash.

```python
# Wrong — compares a bound method object to ""
if str(self.selectedFilesArea.toPlainText) == "":

# Correct
if str(self.selectedFilesArea.toPlainText()) == "":
```

---

### BUG-2 — Copy-paste error in `completeGenome.py:105` (Critical)

**File:** `src/scripts/assembly/utils/completeGenome.py:105`

The function writes the variable `firstPortion` where it should write `lastPortion`. This silently produces an incorrect FASTA output — the last segment of the genome is replaced by a copy of the first segment. The assembly will appear to complete successfully but the output sequence will be wrong.

```python
# Wrong — writes firstPortion twice
outfile.write(">lastPortion\n" + firstPortion + "\n")

# Correct
outfile.write(">lastPortion\n" + lastPortion + "\n")
```

---

### BUG-3 — Hardcoded k-mer length inconsistency in `genotypingQt.py` (High)

**File:** `src/scripts/genotyping/genotypingQt.py:511`

The variable `kmerLength` is defined and used for the k-mer counting loop, but one loop uses a hardcoded `16` instead of `kmerLength`. If the k-mer length is ever changed, this loop will silently produce wrong counts.

```python
# Line 478 — correct, uses variable
for a in range(0, len(sequence) - kmerLength + 1):

# Line 511 — wrong, hardcoded 16
for a in range(0, len(sequence) - 16):
```

---

### BUG-4 — `warnings` variable used before declaration in `annotationQt.py` (High)

**File:** `src/scripts/annotation/annotationQt.py`, around lines 252 and 262

The `warnings` list is referenced before it is initialised (at line ~268). Depending on execution path, this raises a `NameError` at runtime when the annotation encounters certain gene structures.

---

### BUG-5 — `readsFilteringQt.py` hardcodes HCMV genome size in two places (Medium)

**File:** `src/scripts/readsFiltering/readsFilteringQt.py:736` and `:831`

The HCMV genome size (`235646.0`) is hardcoded as a magic number in coverage calculations. If the reference is ever changed or a different virus is used, coverage calculations will be silently wrong. The same literal appears twice (not DRY), so it would need to be changed in both places.

```python
coverage = (float(numMappedReads) * avgReadLength) / 235646.0
```

---

## Per-Module Findings

---

### Module: `src/.GRACy_main.py` (149 lines)

**Ruff flagged:** `VirHosFilt_support` referenced at lines 41 and 43 — this module is never imported and does not exist in the codebase. These are dead code remnants from an earlier version. `installationDirectory` is also flagged as undefined (F821) — it is set in `__main__` but referenced inside nested functions that close over it; this works at runtime but is fragile.

**Issue:** 6 `os.system()` module launch calls with no `shell=False` and no quoting of `installationDirectory`. If the installation path contains spaces, all module launches will fail.

---

### Module: `src/scripts/assembly/assemblyQt.py` (1,320 lines)

Ruff: ~120 violations. Bandit: ~145 injection sites.

- **BUG-1** applies (line 143)
- `performAssembly()` is 1,121 lines — the single largest method in the codebase
- `os.chdir()` is called with no existence check; if `mkdir` fails (CC-1), the subsequent `chdir` will crash with no useful message
- `time.sleep(1)` at line 218 used to wait for a file — fragile, will fail on slow storage
- 10+ blocks of commented-out `os.system()` calls throughout
- `confFiles = []` declared as a class-level variable (line 124) rather than instance variable — shared across all instances

---

### Module: `src/scripts/assembly/assembly.py` (1,134 lines)

Ruff: ~115 violations. Bandit: ~200 injection sites.

- **BUG-1** applies (line 194)
- Near-duplicate of `assemblyQt.py` — the two files have diverged and are not in sync. Shared logic should be extracted into a common module
- `performAssembly()` is 953 lines
- Multiple `exit()` calls (Python 2 style) instead of `sys.exit()`
- Config parsing uses raw string splitting with no validation — a malformed `.conf` silently assigns wrong values to variables

---

### Module: `src/scripts/annotation/annotationQt.py` (1,343 lines)

Ruff: ~95 violations. Bandit: ~20 injection sites.

- **BUG-4** applies (`warnings` used before declaration)
- `runAnnotation()` is ~1,200 lines — the second largest method
- Four output files opened without context managers (CC-4)
- Hardcoded locus `"RL6"` embedded in a logic condition (line ~367) — organism-specific knowledge mixed into generic logic
- Variable `a` reused as loop counter in multiply-nested scopes (lines ~502, ~731, ~914), making logic very hard to follow
- Complex coordinate slicing with no bounds checking — will silently truncate on unusual gene structures

---

### Module: `src/scripts/genotyping/genotypingQt.py` (787 lines)

Ruff: ~60 violations. Bandit: ~30 injection sites.

- **BUG-1** applies (line 194)
- **BUG-3** applies (line 511 — hardcoded k-mer length)
- `runGenotyping()` is 451 lines
- `orderedHyperLoci` list (line 187) hardcodes gene names — should be in a config file
- `colorDict` (line 641) hardcodes colour mappings — reasonable for now but should be noted
- `str(percentage * 100)[:5]` (line 612) — fragile string truncation; will misbehave for values like `100.0` (which is 5 chars) or negative values

---

### Module: `src/scripts/snpCalling/snpCallingQt.py` (586 lines)

Ruff: ~50 violations. Bandit: ~48 injection sites.

- **BUG-1** applies (line 273)
- `runTool()` is 229 lines with 5+ levels of nesting
- Line 358–363: repeated `if` statements (not `elif`) checking file extensions — if a filename matches multiple patterns, multiple code paths execute. Should be `elif`.
- Hardcoded perl module path in one of the tool invocations

---

### Module: `src/scripts/readsFiltering/readsFilteringQt.py` (940 lines)

Ruff: ~85 violations. Bandit: ~65 injection sites.

- **BUG-1** applies (line 302)
- **BUG-5** applies (hardcoded `235646.0` at lines 736 and 831)
- `runTool()` is 577 lines — the longest non-assembly method
- Lines ~643–832 nearly duplicate lines ~469–537 — coverage calculation logic should be extracted into a function
- `os.system("rm -f *.sam *.bam ...")` — wildcard `rm` can delete unintended files if the working directory contains unexpected files
- `os.system("rm -f coverage.txt *140875*")` — the suffix `140875` appears to be a developer-specific random seed or temp file prefix; hardcoded throughout

---

### Module: `src/scripts/dbsubmission/dbsubmissionQt.py` (603 lines)

Bandit: ~8 injection sites.

- **BUG-1** applies (line 319)
- **Critical security issue:** ENA username and password from GUI text fields are concatenated directly into `curl` shell commands (lines 224, 228, 291, 295, 499, 503). A password containing shell metacharacters (e.g. `$`, `` ` ``, `!`) will break the command or expose credentials to shell expansion
- `sys.stdin.read(1)` appears at lines 521 and 546 — this blocks the GUI thread waiting for a keypress. In a PyQt5 GUI this will freeze the window. These appear to be debug `pause` statements that were never removed
- `print("fastqreceipt to transform")` / `print("fastqreceipt transformed")` at lines 509, 513 — debug print statements left in production code
- `time.sleep(3)` at line 449 — arbitrary sleep between ENA API calls; should use response checking
- File `projectReceipt` / `sampleReceipt.txt` opened without context manager; not closed on error path

---

### Module: `src/scripts/assembly/utils/scaffold_builder.py` (570 lines)

- Bare `except: pass` at lines 483 and 569 — silently swallows all exceptions including keyboard interrupt
- Global `parameters` dict (lines 13–15) and `hashSequences` used as module-level globals across functions — makes the module non-reentrant
- One `os.system()` call to `nucmer` with concatenated path parameters — injection risk

---

### Module: `src/scripts/assembly/utils/completeGenome.py` (181 lines)

- **BUG-2** applies (line 105 — `firstPortion` instead of `lastPortion`)
- Hardcoded relative paths `"../2_spadesAssembly/scaffolds.fasta"` (lines 21, 109) — will fail if called from any directory other than the expected one
- Multiple `exit()` calls (lines 38, 89, 181) — Python 2 style, should be `sys.exit()`
- 10+ `os.system()` calls with no return code checking

---

### Module: `src/scripts/assembly/utils/getBestAssembly.py` (86 lines)

- `os.system("rm -rf outputSpades*")` at line 85 — wildcard `rm -rf` will delete any directory starting with `outputSpades` in the current working directory, including any that may have been created by a previous run that the user may have wanted to keep
- `sys.argv[4]` assigned to `installationDirectory` (line 11) but `sys.argv[3]` used as the output file — the non-sequential argument indexing is confusing and error-prone
- Mixed use of `open()` and `with open()` in the same file

---

### Module: `src/scripts/assembly/utils/varscanFilter.py` (138 lines)

- `Seq.reverse_complement()` called (lines 61–62, 98–99) — this is a deprecated API in BioPython; the correct call is on a `Seq` object, not the module function. Will produce a deprecation warning or fail on newer BioPython
- `kmersInReads` initialised as empty list (line 27) but is never populated — the `.count()` calls on lines 61–62 will always return 0, making the kmer-based validation branch always compare 0 vs 0
- 8 `os.system()` calls with no return code checking

---

### Module: `src/scripts/snpCalling/utils/polyAn.py` (277 lines)

- Module-level code runs on import — all the VCF parsing logic (lines 30–277) executes at the top level, not inside functions. This means the script cannot be imported without running analysis
- `line` variable used at line 132 (`while not "#CHROM" in line`) but is never initialised in this scope — will raise `NameError` on first run. The `line` variable from the GFF parsing loop above goes out of scope
- Extensive `print()` debug statements throughout (lines 157, 167–168, 180, 183, 186–189, 202, 204, 238, 240) — these will pollute stdout in production

---

### Module: `src/scripts/annotation/lncRNA_annotation.py` (75 lines)

- All four `os.system()` calls at lines 36–40 use concatenated user-controlled parameters with no quoting
- `makeblastdb` called inside a loop (once per lncRNA sequence) — this rebuilds the BLAST database repeatedly against the same genome. Should be called once before the loop — a significant performance bug on genomes with many lncRNA candidates
- No context manager on any of the three output files

---

### Module: `src/scripts/assembly/utils/changeHeaderFormat.py` (`readsFiltering/utils/`)

- Overwrites `read1` and `read2` in-place via `mv temp1 read1` with no backup — if the script crashes mid-run, the original files are lost and only partial output exists

---

### `install.sh` (416 lines)

- Not idempotent — re-running install on an existing setup may fail or produce inconsistent state
- No error checking after any `conda install` command — a failed package install silently continues
- Line 5: `mv temp` — no error check; if the temp file doesn't exist, subsequent steps will fail
- The entire script is a repetitive pattern of `conda install` + `grep` checks; a loop with an exit-on-failure would be 80% shorter and more reliable

---

## Tooling Recommendations

### Install now: Ruff

**Purpose:** Linter and formatter — finds style, correctness, and maintenance issues in seconds.

**Install:**
```bash
~/.local/bin/pip install --user ruff
```

**Run:**
```bash
~/.local/bin/ruff check src/         # show violations
~/.local/bin/ruff check --fix src/   # auto-fix safe violations
```

Ruff found **436 violations** in this codebase on its default rules. The majority (E712, E713) are auto-fixable in one command. The F821 undefined-name errors point to real structural issues.

**Recommended config** — add to `pyproject.toml` (see below):
```toml
[tool.ruff]
target-version = "py38"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "W"]
ignore = [
    "E501",   # line too long — address separately
]
```

Once the auto-fixable violations are cleared, gradually enable `"B"` (bugbear), `"C4"` (comprehensions), and `"UP"` (pyupgrade) rule groups.

---

### Install now: Bandit

**Purpose:** Security scanner — finds shell injection, dangerous functions, and weak crypto.

**Install:**
```bash
~/.local/bin/pip install --user bandit
```

**Run:**
```bash
~/.local/bin/bandit -r src/ -f txt
~/.local/bin/bandit -r src/ -f txt --severity-level high  # high-severity only
```

Bandit found **916 issues** — 579 of them are definite shell injection risks (B605). The B607 findings (167) flag `os.system()` calls that use partial paths (tool name without full path — these are actually using full `installationDirectory`-prefixed paths, so the B607 findings are mostly false positives once `os.system()` is replaced with `subprocess`).

**Recommended `.bandit` config** to suppress known false positives:
```ini
[bandit]
skips = B607
```

---

### Defer: mypy

Full type checking requires annotating all 6,000+ lines before it provides value. Recommended approach: run in report-only mode to baseline the scope, then annotate incrementally starting with non-GUI utility modules (`biomodule.py`, `varscanFilter.py`, `getBestAssembly.py`).

```bash
~/.local/bin/pip install --user mypy
mypy src/ --ignore-missing-imports --no-error-summary 2>&1 | tail -5
```

---

### One-off: Pyupgrade

Run once to modernise Python 2/3 compatibility shims:
```bash
~/.local/bin/pip install --user pyupgrade
find src/ -name "*.py" | xargs pyupgrade --py3-plus
```

---

### Skip: Pylint, Flake8

Pylint is too verbose on legacy PyQt5 codebases. Flake8 is entirely superseded by Ruff.

---

### Optional: pre-commit

If RS is also committing code, add a `.pre-commit-config.yaml` to enforce Ruff on every commit:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.13
    hooks:
      - id: ruff
        args: ['--fix']
      - id: ruff-format
```

Install: `pip install pre-commit && pre-commit install`

---

## Conclusions and Links to TASKS.md

The review confirms and quantifies the issues identified in Phase 1. The five confirmed bugs should be treated as **immediate hotfixes** regardless of where Phase 3 prioritisation lands.

| Bug | File | Recommended action |
|-----|------|--------------------|
| BUG-1 `toPlainText()` missing `()` | 5 modules | Fix now — 1 line each |
| BUG-2 `firstPortion` copy-paste | `completeGenome.py:105` | Fix now — 1 line |
| BUG-3 hardcoded kmer length | `genotypingQt.py:511` | Fix now — 1 line |
| BUG-4 `warnings` undefined | `annotationQt.py` | Fix in Phase 5 |
| BUG-5 hardcoded genome size | `readsFilteringQt.py` | Fix in Phase 5 |

Existing candidate tasks confirmed and strengthened by this review:

| TASK | Finding |
|------|---------|
| TASK-010 | 579 definite injection sites quantified by Bandit |
| TASK-011 | Methods of 229–1,204 lines across all modules |
| TASK-012 | 916 unchecked `os.system()` calls; no exception handling anywhere |
| TASK-013 | Python 2 shims confirmed in multiple files |
| TASK-016 | `.gitignore` missing — AppleDouble `._*.py` files still committed |
| TASK-017 | 13 AppleDouble files confirmed present; skipped by both tools |
| TASK-018 | Commented dead code confirmed in every module |

New candidate tasks surfaced by this review:

| ID | Task | Severity |
|----|------|----------|
| TASK-021 | Fix BUG-1: add `()` to `toPlainText` in all 5 modules | Critical |
| TASK-022 | Fix BUG-2: `firstPortion` → `lastPortion` in `completeGenome.py:105` | Critical |
| TASK-023 | Fix BUG-3: replace hardcoded `16` with `kmerLength` in `genotypingQt.py:511` | High |
| TASK-024 | Fix `sys.stdin.read(1)` debug pauses in `dbsubmissionQt.py` (lines 521, 546) | High |
| TASK-025 | Fix `makeblastdb` called in loop in `lncRNA_annotation.py` — rebuild once only | High |
| TASK-026 | Remove debug `print()` statements from `polyAn.py` and `dbsubmissionQt.py` | Medium |
| TASK-027 | Add Ruff + Bandit to project and document baseline in `pyproject.toml` | Low |
| TASK-028 | Fix `varscanFilter.py` deprecated `Seq.reverse_complement()` API call | Medium |
