# Phase 1 — Architecture Review

**Owner:** IK  
**Status:** In Progress  
**Baseline:** See `archive/code_analysis/ARCHITECTURE.md` for the structural overview already completed.

---

## Scope

This review builds on the baseline architecture document and goes deeper on **structural risks** — things that would block refactoring, testing, or future development. It is not a repeat of what's already documented.

## Questions to Answer

1. **GUI/logic coupling** — How deeply is pipeline logic entangled with Tkinter/PyQt5 widgets? Is a headless/CLI mode achievable without a full rewrite?
2. **Inter-module contracts** — What are the exact file formats passed between pipeline stages? Are they documented anywhere, or implicit?
3. **Utility script architecture** — The 17 assembly utilities are called via `os.system()` with `sys.argv`. Which ones could be imported as Python modules instead?
4. **State management** — Where does shared state live between pipeline steps? Is it only files, or are there global variables?
5. **Dual UI risk** — The Tkinter and PyQt5 versions appear to share logic. Are they truly in sync, or have they diverged?

## Findings

### Q1 — GUI/Logic Coupling

**Severity: High**

The GUI and pipeline logic are inseparably entangled in `assemblyQt.py`. The entire pipeline runs inside `performAssembly()` (lines 142–1309), which reads widget values inline at 8+ points during execution (e.g. `self.memoryCombo.currentText()` at lines 289, 372, 422, 776, 821, 925, 965, 1035; `self.numThreadsCombo.currentText()` at lines 371, 394, 564, 632 and more). Roughly 80 interspersed `self.logArea.append() / self.logArea.repaint()` calls are scattered throughout the pipeline steps — these provide live progress feedback but tightly couple execution to a running Qt widget.

Of the 1,320 lines in `assemblyQt.py`, approximately 110 lines are pure UI setup (widget instantiation and layout); the remaining ~1,210 lines are pipeline logic polluted with ~303 `self.` widget references.

**Headless/CLI feasibility:** Achievable without a full rewrite, via a callback-based refactor — replacing `self.logArea.append/repaint()` calls with a `progress_callback(message)` argument and widget reads with function parameters. Confirmed: there are no `processEvents()` or `QEventLoop` calls inside `performAssembly()` — only two `exec_()` calls exist in the file, at line 150 (a message dialog outside the pipeline) and line 1319 (the standard Qt main loop entry). The pipeline does not depend on the Qt event loop to make progress. However, the `os.chdir()` pattern (see Q4) adds a constraint: any headless caller must manage working directory carefully.

**Headless mode is a stated future goal** (not a current requirement). The coupling is therefore medium-high priority: it blocks unit testing today and headless use tomorrow.

---

### Q2 — Inter-Module Contracts

**Status: Entirely implicit. No formal documentation exists.**

There is no pipeline orchestrator, no shared project state, and no automatic handoff between modules. Each module is launched independently. Users must manually locate and supply output files from one module as inputs to the next. The six modules function as six separate tools, not a connected pipeline.

**Contract map:**

| Module | Input | How supplied | Output |
|--------|-------|-------------|--------|
| Reads Filtering | Raw paired FASTQ (`*_1.fastq`, `*_2.fastq`) | User selects via dialog | `{name}_nh_1.fastq / _nh_2.fastq`, `_tr_*`, `_dd_*` to user-chosen folder |
| Assembly | Config file listing FASTQ paths; expects reads in `./1_cleanReads/` | User provides `.conf` file | `{projectName}_genome.fasta`, `*.bam`, `*.vcf`, coverage plots — written into numbered subdirs |
| Genotyping | Paired FASTQ (`*_1.fastq`, `*_2.fastq`) | User selects via dialog; **no connection to Assembly output** | Genotyping report |
| SNP Calling | Paired FASTQ (`*_1.fastq` / `*_2.fastq` or `*_R1_001.fastq`) | User selects via dialog | Filtered VCF, SNP table, heatmap PNG |
| Annotation | Assembled FASTA (`*.fasta`) | User selects via dialog | `{genome}_annotation.gff`, `_cds.fasta`, `_proteins.fasta`, `_annotationWarnings.txt` |
| DB Submission | FASTQ.gz files + project/sample/reads info files | User selects each individually | `project.xml`, `*_sample.xml`, submission package |

Contract encoding is entirely in code: hardcoded directory names (`1_cleanReads/`, `2_spadesAssembly/`, `3_scaffoldsOrientation/`, `4_createConsensus/`, `5_refineAssembly/`, `6_createConsensus/`), magic filename suffixes (`_nh`, `_tr`, `_dd`, `_hq`), and hardcoded relative paths (e.g. Assembly checks for `../2_spadesAssembly/scaffolds.fasta` in `completeGenome.py`).

---

### Q3 — Utility Script Importability

The `src/scripts/assembly/utils/` directory contains 20 files (18 `.py` scripts + 2 non-Python files: `GapFiller`, `vcf-sort`). Classification of the 18 Python scripts:

| Script | Class | Notes |
|--------|-------|-------|
| `scaffold_builder.py` | **B** | Full function library; module-level execution block at bottom needs `if __name__ == "__main__"` guard. ~30 min. |
| `revComp.py` | **B** | 4-line script; trivially wrappable as a function. ~15 min. |
| `varscanFilter.py` | **B** | Uses argparse; logic runs at module level via `args = vars(parser.parse_args())`. Wrap in `main()` + guard. ~30 min. |
| `cleanSoftAndUnmapped.py` | **C** | Opens and writes files at module level immediately after `sys.argv`. Needs function extraction. |
| `completeGenome.py` | **C** | Reads FASTA and opens output files at module level. Needs function extraction. |
| `completeGenome2.py` | **C** | Has `fuseSequences2()` function but also runs `os.system()` at module level. Needs function extraction. |
| `createCenterScaffold.py` | **C** | Calls `os.system()` at module level immediately — 10+ tool invocations before any function. |
| `extractSeqByRange.py` | **C** | Opens output file at line 2 of module. Needs function extraction. |
| `gapPrediction.py` | **C** | Calls `os.system()` at module level. |
| `getBestAssembly.py` | **C** | Opens output file at module level; calls `os.system()` inline. |
| `getMajorAllele.py` | **C** | Opens input/output files at module level. |
| `joinScaffolds.py` | **C** | Reads `sys.argv` then runs algorithm at module level. |
| `joinScaffolds_careful.py` | **C** | Same pattern as `joinScaffolds.py`. |
| `joinScaffolds_trivial.py` | **C** | Same pattern. |
| `maskLowCoverage.py` | **C** | Reads FASTA and opens output file at module level. |
| `mergeQualFilteredMates.py` | **C** | Reads `sys.argv` and sets up data structures at module level. |
| `runQualityFiltering.py` | **C** | Defines a class then reads sys.argv and runs logic at module level. |
| `splitIntervealed.py` | **C** | Opens files at module level immediately. |

**Summary:** 3 scripts (Class B) can be made importable with ~30 min of surgery each. 15 scripts (Class C) require function extraction — each is straightforward (10–60 min per script) but there are many of them.

---

### Q4 — State Management

**Finding: Primarily filesystem-based. No cross-module globals. `os.chdir()` is a constraint.**

There is one module-level global in each module file: `installationDirectory = sys.argv[1]`, which is read-only after startup. No mutable globals exist.

All inter-step state flows through the filesystem via numbered subdirectories (`1_cleanReads/`, `2_spadesAssembly/`, etc.). Each pipeline step reads from the previous step's output directory and writes to its own.

The one structural risk is `os.chdir()`. Both `assembly.py` and `assemblyQt.py` use `os.chdir()` extensively (13 calls each) to navigate between numbered subdirectories. Since each module runs as a separate OS process, this is safe today — the chdir only affects that process. However, if any future refactor moves modules in-process (e.g. into a single headless runner), the chdir calls would corrupt shared working directory state. Any headless extraction plan must address this — either replace chdir with absolute paths throughout, or spawn each step in a subprocess.

---

### Q5 — Dual UI Divergence

**Finding: `assembly.py` is orphaned dead code with a deeper divergence than anticipated.**

The main launcher (`src/.GRACy_main.py` line 58) calls `assemblyQt.py` exclusively. `assembly.py` is not imported or invoked anywhere in the codebase. There are no other references to `assembly.py` in `src/`.

Two utility files referenced by `assembly.py` — `retrieveNodes.py` and `getSequenceFromFasta.py` — do not exist in `src/scripts/assembly/utils/`. `assembly.py` would fail at runtime if anyone attempted to run it directly.

**Variant-caller comparison:** The apparent algorithmic divergence (bcftools/lofreq in Qt version vs VarScan in Tkinter version) is less severe than it appears. All bcftools and lofreq invocations in `assemblyQt.py` are commented out (lines 527–528, 595–596, 662–663, 1000–1001, 1065–1066, 1134–1135). Both versions use VarScan as the active variant caller. `bcftools consensus` IS active in `assemblyQt.py` (to apply the VCF to produce the final genome), which `assembly.py` does not have — this is a real, functional difference in how the consensus is built.

**Additional dead-code finding:** `assemblyQt.bak` (a backup of assemblyQt.py from a prior edit) is committed to the repo. Combined with `assembly.py`, there are three versions of the assembly pipeline in the codebase: one active, two dead.

---

## Conclusions

### Critical blocker for testing and future refactoring

**GUI/logic coupling in `assemblyQt.py`** (Q1) is the single highest-priority structural problem. No function in the assembly pipeline can be unit-tested without launching a PyQt5 application. Extracting `performAssembly()` into a standalone function with a progress callback is the prerequisite for any test harness and for future headless use. The `os.chdir()` pattern (Q4) must be resolved in the same pass — replace with absolute path construction to eliminate the working-directory side-effect.

### Dead code to resolve

`assembly.py`, `assemblyQt.bak`, and references to two non-existent utility scripts (`retrieveNodes.py`, `getSequenceFromFasta.py`) should be investigated and cleaned up. `assembly.py` would fail if run. Status is **uncertain** — TASK-025 covers the investigation and deletion decision.

### Inter-module contracts: formalise before any refactor

All six inter-module contracts are implicit (Q2). Before any module-level API change, these should be documented using the compound-engineering skill. The most fragile contract is Reads Filtering → Assembly: the Assembly module hardcodes a relative path (`./1_cleanReads/qualityFiltered_1.fq`) that must be populated by the user manually. This is a usability risk as well as a maintenance risk.

### Utility scripts: quick wins available

Three Class-B scripts (`scaffold_builder.py`, `revComp.py`, `varscanFilter.py`) can be made importable with minimal effort (~30 min each). These are the right first targets if the goal is to start replacing `os.system()` calls with in-process function calls. The 15 Class-C scripts require function extraction; they should be addressed as part of TASK-011 (extract pipeline logic) rather than separately.

### State management: no action needed

Filesystem-based state with no mutable globals is sound design for this architecture. The `os.chdir()` pattern is safe in the current child-process model; it only needs addressing if modules are ever consolidated into a single process (see headless work).

### Feed into TASKS.md

| Proposed ID | Task | Area | Severity |
|-------------|------|------|----------|
| TASK-021 | Formalise inter-module file contracts using compound-engineering skill (naming conventions, directory layout, FASTQ format expectations) | All modules | Medium |
| TASK-022 | Extract `performAssembly()` from `assemblyQt.py` into standalone function with progress callback; replace inline `os.chdir()` with absolute path construction | `assembly/` | High |
| TASK-023 | Add `if __name__ == "__main__"` guard to `scaffold_builder.py`, `revComp.py`, `varscanFilter.py` (Class-B scripts) | `assembly/utils/` | Low |
| TASK-024 | Extract functions in all 15 Class-C utility scripts to enable import | `assembly/utils/` | Medium |
| TASK-025 | Investigate `assembly.py` orphan: confirm missing utils, compare consensus-building step vs `assemblyQt.py`, then decide delete vs archive | `assembly/` | Medium |
