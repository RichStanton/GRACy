# GRACy Improvement — Task Tracker

## In Progress

| ID | Task | Owner |
|----|------|-------|
| TASK-004 | Phase 4: IK/RS review and decisions | IK + RS |

---

## Backlog

### Project Phases

| ID | Task | Owner | Depends On |
|----|------|-------|------------|
| TASK-005 | Phase 5: Implementation — changes + test harnesses | IK | TASK-004 |

### Candidate Code Tasks
*Prioritised in Phase 3 — see `planning/priority_plan.md` for ordering rationale. Await IK/RS decisions (TASK-004) before implementation begins.*

| ID | Task | Area | Severity |
|----|------|------|----------|
| TASK-010 | Replace `os.system()` with `subprocess.run()` and check return codes | All modules | High |
| TASK-011 | Extract pipeline logic out of `Toplevel1.__init__()` into testable functions | All modules | High |
| TASK-012 | Add error logging and halt-on-failure behaviour | All modules | High |
| TASK-013 | Collapse Python 2 conda environment (ragout now supports Python 3) | `install.sh` | Medium |
| TASK-014 | Remove Miniconda installer binaries from repo; download at install time | `install.sh` | Medium |
| TASK-015 | Build initial test harness for assembly pipeline | `assembly/` | Medium |
| TASK-016 | Fix `.gitignore` — add `.DS_Store`, `._*`, Miniconda `.sh` files | `.gitignore` | Low |
| TASK-017 | Delete committed AppleDouble `._*.py` files | Throughout | Low |
| TASK-018 | Remove commented-out dead code | Throughout | Low |
| TASK-019 | Fix 4 typos in log/UI messages | `assembly.py` | Low |
| TASK-020 | Write proper README with install instructions for this fork | `README.md` | Low |

### Hotfixes — Confirmed bugs from Phase 2 code review
*These are correctness bugs. Fix before Phase 3 prioritisation.*

| ID | Task | Area | Severity |
|----|------|------|----------|
| TASK-021 | Fix BUG-1: add `()` to `toPlainText` in all 5 modules | 5 `*Qt.py` files | Critical |
| TASK-022 | Fix BUG-2: `firstPortion` → `lastPortion` in `completeGenome.py:105` | `assembly/utils/` | Critical |
| TASK-023 | Fix BUG-3: replace hardcoded `16` with `kmerLength` in `genotypingQt.py:511` | `genotyping/` | High |
| TASK-024 | Remove `sys.stdin.read(1)` debug pauses in `dbsubmissionQt.py` (lines 521, 546) | `dbsubmission/` | High |
| TASK-025 | Fix `makeblastdb` called in loop in `lncRNA_annotation.py` — call once before loop | `annotation/` | High |
| TASK-026 | Remove debug `print()` statements from `polyAn.py` and `dbsubmissionQt.py` | `snpCalling/`, `dbsubmission/` | Medium |
| TASK-027 | Add Ruff + Bandit to project and document baseline in `pyproject.toml` | Project root | Low |
| TASK-028 | Fix deprecated `Seq.reverse_complement()` API call in `varscanFilter.py` | `assembly/utils/` | Medium |

### Architecture-Derived Tasks — from Phase 1 architecture review

| ID | Task | Area | Severity |
|----|------|------|----------|
| TASK-029 | Formalise inter-module file contracts using compound-engineering skill (naming conventions, directory layout, FASTQ format expectations) | All modules | Medium |
| TASK-030 | Extract `performAssembly()` from `assemblyQt.py` into standalone function with progress callback; replace inline `os.chdir()` with absolute path construction | `assembly/` | High |
| TASK-031 | Add `if __name__ == "__main__"` guard to `scaffold_builder.py`, `revComp.py`, `varscanFilter.py` (Class-B utils — enables import) | `assembly/utils/` | Low |
| TASK-032 | Extract functions in all 15 Class-C utility scripts to enable import | `assembly/utils/` | Medium |
| TASK-033 | Delete `assembly.py` and `assemblyQt.bak` — confirmed dead code (arch review: not called anywhere, references two non-existent utils; no investigation needed) | `assembly/` | Medium |

---

## Done

| ID | Task | Completed |
|----|------|-----------|
| TASK-000 | Set up agent workspace structure | 2026-05-20 |
| TASK-001 | Phase 1: Architecture review | 2026-05-20 |
| TASK-002 | Phase 2: Code review | 2026-05-20 |
| TASK-003 | Phase 3: Create prioritised list of changes | 2026-05-20 |
