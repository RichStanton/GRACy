# GRACy Improvement Project — Executive Summary

**Owner:** Iain Keddie (IK)
**Reviewer:** Richard Stanton (RS)
**Date:** 2026-05-20
**Status:** Phases 1–3 complete. Phase 4 (IK/RS decisions) ready to begin.

---

## What This Project Is

GRACy is a bioinformatics desktop application for end-to-end HCMV (Human Cytomegalovirus) genome analysis. It wraps approximately 25 command-line bioinformatics tools (SPAdes, Bowtie2, BWA, BLAST, VarScan, LoFreq, Samtools, and others) behind a point-and-click PyQt5 GUI, covering the full workflow from raw sequencing reads through to ENA database submission. The tool is aimed at wet-lab scientists who are not command-line proficient.

This project was initiated to systematically assess the codebase and produce a structured improvement plan. The work covers ~7,000 lines of Python across 20+ source files. No code changes have been made yet — the current phases are exclusively analysis and planning.

---

## Part 1 — Project Management Infrastructure

### What Was Created

A self-contained project management workspace was established inside the repository at `agent_workspace/`. It is tracked in version control and is designed to be readable and maintainable independently of the codebase it describes.

**Folder structure:**

```
agent_workspace/
├── README.md              Project overview, phases, participants, workflow rules
├── ARCHITECTURE.md        Full architecture reference document (see Part 2)
├── initial_review.md      Baseline code review (pre-project)
├── planning/
│   ├── architecture_review.md   Phase 1 findings (structural risk review)
│   ├── code_review.md           Phase 2 findings (static analysis + manual review)
│   ├── priority_plan.md         Phase 3 output (prioritised work plan)
│   ├── decisions.md             Phase 4 template (IK/RS decisions — not yet started)
│   └── executive_summary.md     This document
├── tasks/
│   └── TASKS.md           Single source of truth for all work items and their status
├── sessions/
│   └── 2026-05-20.md      Log of what was done in each working session
├── compound/
│   └── README.md          Template for capturing learnings after each phase completes
├── output/
│   ├── Architecture_Review.docx   Customer-ready Word document
│   ├── Code_Review.docx           Customer-ready Word document
│   └── Priority_Plan.docx         Customer-ready Word document
└── md_to_docx.py          Script to regenerate Word documents from planning markdown files
```

**CLAUDE.md** was also created at the project root. This is a persistent instruction file that gives an AI coding assistant full context about GRACy's architecture, install process, module patterns, and conventions — so that any future coding session starts with complete knowledge of the project rather than re-deriving it from scratch.

### Process and Workflow

The project follows a phased approach with a defined workflow at each transition:

| Phase | Description | Owner | Status |
|-------|-------------|-------|--------|
| 1 | Architecture review — structural fundamentals | IK | Complete |
| 2 | Code review — static analysis and manual inspection | IK | Complete |
| 3 | Prioritised list of changes | IK | Complete |
| 4 | Review decisions | IK + RS | **Ready to begin** |
| 5 | Implementation — changes and test harnesses | IK | Not started |

At each phase transition a session log is written to `sessions/YYYY-MM-DD.md`, recording what was done, key findings, decisions made, and what comes next. This means the project state can be picked up by any contributor at any point without needing a verbal handover.

**TASKS.md** is the single source of truth for all work items. It uses a three-section structure (In Progress / Backlog / Done) and records task IDs, descriptions, owners, and dependencies. New tasks discovered during analysis are added immediately so nothing is lost between sessions.

**The decisions.md template** at `planning/decisions.md` is ready for Phase 4. It provides a structured table for recording each task decision (Accept / Defer / Reject / Accept with reduced scope) with reasoning. The intent is for IK and RS to work through the Phase 3 priority plan together in one session and populate this document before any implementation begins.

### Word Document Generation

A Python script (`md_to_docx.py`) converts all planning documents to professionally formatted Word documents for external sharing. It applies consistent branding (navy/steel-blue colour scheme, Calibri body, table styling, code block formatting). To regenerate after any planning document is updated, run:

```bash
cd agent_workspace && python3 md_to_docx.py
```

Output files land in `agent_workspace/output/`. The `decisions.md` file is excluded from generation (it is an internal working document).

---

## Part 2 — Technical Analysis: What Was Found

### Architecture Document (`ARCHITECTURE.md`)

A comprehensive reference document was produced covering:

- Full annotated directory structure of the repository
- Application startup model and process architecture (Tkinter launcher → separate child processes per module)
- Detailed description of all six pipeline modules (Reads Filtering, Assembly, Genotyping, SNP Calling, Annotation, DB Submission)
- Data flow diagram showing inputs, outputs, and inter-module file contracts
- External tool inventory (~25 tools across two Conda environments)
- Known issues and technical debt catalogue
- Quick-reference table for "where to look to change X"

This document is intended as a permanent onboarding reference. It describes the codebase as it currently exists, not as it should be.

---

### Phase 1 — Architecture Review (`planning/architecture_review.md`)

A structural risk assessment targeting five questions:

**Q1 — GUI/Logic coupling (High severity)**
The entire assembly pipeline — 1,121 lines — runs inside a single GUI method (`performAssembly()`), with approximately 303 direct widget references interspersed throughout. This makes it impossible to run any pipeline step headlessly, from tests, or from a command line. The good news: the pipeline does not depend on the Qt event loop to make progress (no `processEvents()` calls), so a refactor using a callback pattern is feasible without a full rewrite.

**Q2 — Inter-module contracts (No formal documentation exists)**
All six modules communicate via files, but the file naming conventions, directory layouts, and expected paths are entirely implicit — encoded as hardcoded strings scattered through the source. No documentation of what one module produces or what the next expects. The most fragile handoff is Reads Filtering → Assembly, where the Assembly module hardcodes a relative path (`./1_cleanReads/qualityFiltered_1.fq`) that must be populated manually by the user.

**Q3 — Utility script importability**
18 Python utility scripts in `assembly/utils/` are called via `os.system()`. Three (Class B) can be made importable with ~30 minutes of work each — they have function structure but lack a `__main__` guard. The remaining 15 (Class C) run analysis at module level and require function extraction before they can be imported or tested.

**Q4 — State management (Sound, with one constraint)**
All state flows through the filesystem via numbered subdirectories. No mutable globals. The one structural risk is `os.chdir()` — called 13 times in `assemblyQt.py` — which is safe today (each module is a separate OS process) but would corrupt shared state if modules were ever consolidated in-process.

**Q5 — Dual UI divergence**
`assembly.py` (the Tkinter version) is confirmed dead code: it is not called from anywhere, references two utility files that do not exist (`retrieveNodes.py`, `getSequenceFromFasta.py`), and would fail at runtime. `assemblyQt.bak` (a backup file) is also committed to the repository. Both can be deleted.

---

### Phase 2 — Code Review (`planning/code_review.md`)

Static analysis was run across all Python source files using two tools:

| Tool | Findings |
|------|----------|
| Ruff 0.15.13 | 436 violations (style, correctness, unused code) |
| Bandit 1.9.4 | 916 security findings (579 definite shell injection) |

**Five confirmed correctness bugs were identified:**

| Bug | File | Impact |
|-----|------|--------|
| BUG-1: `toPlainText` missing `()` in 5 modules | All Qt modules | File-selection guard never fires; clicking Run without files causes unhandled crash |
| BUG-2: `firstPortion` written instead of `lastPortion` | `completeGenome.py:105` | Every assembly produces a silently wrong FASTA — last genome segment replaced by first |
| BUG-3: Hardcoded `16` instead of `kmerLength` variable | `genotypingQt.py:511` | K-mer counts always use 16-mers regardless of user setting |
| BUG-4: `warnings` variable used before declaration | `annotationQt.py` | `NameError` crash on certain gene structures |
| BUG-5: HCMV genome size hardcoded in two places | `readsFilteringQt.py` | Coverage calculations silently wrong if reference genome changes |

**Eight cross-cutting issues affect every module without exception:**

| Issue | Severity |
|-------|----------|
| `os.system()` return codes never checked — tool failures are silent | Critical |
| 579 shell injection sites — user file paths concatenated directly into shell commands; any space in a path breaks the pipeline | Critical |
| All pipeline logic embedded in single God methods (229–1,200 lines each) — untestable, unreusable | High |
| No file context managers — `open()` calls never guaranteed to close on exception | High |
| No exception handling anywhere | High |
| 210 comparison anti-patterns (`== True`, `not x in y`) — auto-fixable by Ruff | Medium |
| No type annotations or docstrings | Medium |
| Python 2 compatibility shims still present | Low |

**Additional module-specific findings of note:**
- `dbsubmissionQt.py`: ENA credentials (username and password) passed raw through shell commands — a password containing `$` or backticks would expose credentials to shell expansion
- `dbsubmissionQt.py`: two `sys.stdin.read(1)` debug pause statements left in production code — freeze the GUI thread
- `lncRNA_annotation.py`: BLAST database rebuilt inside a loop once per candidate — should be built once
- `varscanFilter.py`: deprecated BioPython API call — fails or warns on recent BioPython
- `polyAn.py`: ~15 debug `print()` statements throughout; all analysis logic runs at module level (cannot be imported)

A `pyproject.toml` with Ruff configuration and a `.bandit` config file were created at the project root as part of this phase, establishing a linting baseline.

---

### Phase 3 — Priority Plan (`planning/priority_plan.md`)

A prioritised 8-tier work plan was produced, ordered by effort-to-value ratio with extra weight given to quality tooling (linting, testing infrastructure). Key features of the ordering:

- **Tier 1 (30 minutes):** The three one-line correctness bugs (BUG-1, BUG-2, BUG-3). These are fix-before-anything-else items.
- **Tier 2 (2 hours):** Install Ruff, auto-fix 210 comparison anti-patterns in one command, commit `pyproject.toml`. Quality infrastructure that multiplies the benefit of every future change.
- **Tier 3 (3 hours):** Isolated cleanup — remove debug pauses and print statements, fix the `makeblastdb` loop, fix the BioPython deprecation, delete confirmed dead code (`assembly.py`, `assemblyQt.bak`).
- **Tier 4 (2 days):** Subprocess migration — replace all `os.system()` calls with `subprocess.run()` with return code checking. Eliminates 579 injection sites and silent failures. Ordered to address the credentials security issue first.
- **Tier 5 (2 hours, alongside Tier 4):** Replace bare `open()` calls with context managers.
- **Tier 6 (half day):** Document all six inter-module contracts before any API-changing refactoring begins.
- **Tier 7 (1–2 weeks):** Extract pipeline logic from GUI classes into testable standalone functions; fix `os.chdir()` in the same pass; build first unit test harness for the assembly module.
- **Tier 8 (deferred):** Python 2 environment collapse, type annotations, README rewrite, minor typos.

---

## Part 3 — Current State and Next Steps

### What has been completed

- Full architecture document (permanent onboarding reference)
- Phase 1: structural risk assessment (5 questions answered, 5 new tasks added to tracker)
- Phase 2: full code review with static analysis (5 confirmed bugs, 8 systemic patterns, per-module findings for all 20 files)
- Phase 3: prioritised 8-tier work plan combining both reviews
- Linting baseline committed (`pyproject.toml`, `.bandit`)
- All 33 candidate tasks documented and tracked in `TASKS.md`
- Three Word documents generated for external distribution

### No code has been changed yet

All work to date is analysis and planning. The five confirmed bugs are documented and ready to fix — each is a 1-line change — but no implementation has been carried out pending the Phase 4 IK/RS decisions session.

### Immediate next step — Phase 4 decisions session

IK and RS should review `planning/priority_plan.md` (or `output/Priority_Plan.docx`) together and populate `planning/decisions.md` with Accept/Defer/Reject decisions for each tier. This session is the gate before any implementation begins.

**Recommended reading order for Phase 4:**
1. This document (context)
2. `output/Priority_Plan.docx` (the ranked work list)
3. `output/Architecture_Review.docx` and `output/Code_Review.docx` (supporting evidence for specific items)

After Phase 4, implementation can begin in Phase 5, starting with the Tier 1 one-line bug fixes.
