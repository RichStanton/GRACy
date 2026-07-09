# GRACy — Architecture Document

## Overview

**GRACy** (Genome Research Assistant for CytomegaloVirus) is a desktop bioinformatics pipeline application for end-to-end HCMV (Human Cytomegalovirus) genome analysis. It wraps ~25 command-line bioinformatics tools in a two-layer GUI (Tkinter launcher + PyQt5 module windows) and orchestrates them via `os.system()` calls. The application targets Linux HPC environments and wet-lab scientists who are not command-line proficient.

**Tech stack:** Python 3 (+ Python 2 legacy env), Tkinter, PyQt5, BioPython, Matplotlib, BLAST, Bowtie2, BWA, SPAdes, Lofreq, VarScan, Trim-galore, Jellyfish, Samtools, Seqtk, Fastuniq.

**Platform:** Linux only (no Windows/macOS support despite partial `sys.platform` checks).

---

## Directory Structure

```
GRACy/
├── GRACy.py                        # Entry point — Tkinter main window launcher
├── install.sh                      # Bash installer (Miniconda + all tool deps)
├── LICENSE.txt                     # GPL3
├── README.md                       # Minimal (2 sentences)
├── GRACy manual.pdf                # User documentation
├── data/
│   ├── assembly.conf               # Example assembly config (INI-style key=value)
│   ├── ENA submission worksheet.xlsx
│   └── merlinReference/            # HCMV Merlin strain reference genome
│       ├── hcmv_genome.fasta       # Reference sequence
│       ├── hcmv_genome.fasta.*     # BLAST indices
│       ├── *.bt2                   # Bowtie2 indices
│       └── merlinGenome_*.txt      # Segment annotations
├── src/
│   ├── .GRACy_main.py              # Tkinter UI definition (imported by GRACy.py)
│   ├── GUI/
│   │   ├── IconsFinal/             # 6 PNG module icons
│   │   └── *.jpg                   # Screenshot docs
│   └── scripts/
│       ├── utils/
│       │   └── biomodule.py        # Shared: reverseComplement(), ambiguityCode()
│       ├── readsFiltering/
│       │   ├── readsFilteringQt.py # PyQt5 GUI for read QC
│       │   ├── readsQualityCheck.py
│       │   └── utils/changeHeaderFormat.py
│       ├── assembly/
│       │   ├── assembly.py         # 1,133-line monolithic pipeline backend
│       │   ├── assemblyQt.py       # PyQt5 GUI
│       │   ├── assembly.conf       # Config template
│       │   └── utils/              # 17 utility scripts (see below)
│       ├── genotyping/
│       │   ├── genotyping.py       # K-mer species/strain identification
│       │   ├── genotypingQt.py     # PyQt5 GUI
│       │   ├── fastaFiles/         # Species reference sequences
│       │   └── kmerDB/             # Pre-built k-mer databases
│       ├── snpCalling/
│       │   ├── snpCalling.py       # SNP calling and analysis
│       │   ├── snpCallingQt.py     # PyQt5 GUI
│       │   └── utils/
│       │       ├── buildTable.py
│       │       ├── plotHeatmap.py
│       │       ├── polyAn.py
│       │       └── trimPolyN.py
│       ├── annotation/
│       │   ├── annotation.py       # Gene annotation via BLAST
│       │   ├── annotationQt.py     # PyQt5 GUI
│       │   ├── lncRNA_annotation.py
│       │   └── proteinDB/          # BLAST protein DBs for ~20 HCMV genes
│       └── dbsubmission/
│           ├── dbsubmission.py     # ENA database submission
│           ├── dbsubmissionQt.py   # PyQt5 GUI
│           └── utils/annotationChecklist.txt
└── testDataset/                    # Intended test data (currently empty)
```

### Assembly Utilities (`src/scripts/assembly/utils/`)

| File | Purpose |
|------|---------|
| `scaffold_builder.py` | Needleman-Wunsch reference-guided scaffolding |
| `completeGenome.py` / `completeGenomeV2.py` | Gap filling between scaffolds |
| `joinScaffolds.py` / `joinScaffoldsV2.py` / `joinScaffoldsV3.py` | Scaffold joining variants |
| `cleanSoftAndUnmapped.py` | SAM/BAM filtering (remove soft-clipped + unmapped) |
| `getBestAssembly.py` | Rank assemblies by N50 metric |
| `varscanFilter.py` | VCF variant filtering |
| `changeHeaderFormat.py` | FASTA header normalization |
| (9 others) | Minor preprocessing/formatting helpers |

---

## Application Startup & Process Model

```
User runs: ./GRACy.py
    │
    └─→ GRACy.py (Tkinter)
            └─→ src/.GRACy_main.py (UI window class: Toplevel1)
                    │
                    ├─ Reads INSTALLATION_DIRECTORY from sys.argv[1]
                    │   (set by install.sh shebang rewrite)
                    │
                    └─ 6 clickable module buttons, each calls:
                       os.system("python <installDir>/src/scripts/<module>/<module>Qt.py <installDir>")
                       (each spawns a SEPARATE Python process)
```

**Critical design point:** Each module runs as an independent child process. There is no shared in-memory state between modules — they communicate via files on disk. The `installDir` path is passed as `sys.argv[1]` to every child so they can locate bundled databases and reference files.

---

## Six Pipeline Modules

### Module 1 — Reads Filtering (`readsFiltering/`)

**Entry:** `readsFilteringQt.py` → `readsQualityCheck.py`

**What it does:**
- Trims low-quality bases from raw FASTQ reads (Trim-galore / Cutadapt)
- Filters by minimum mean quality, minimum length, uniqueness
- Removes duplicate reads (Fastuniq)
- Normalizes FASTA headers (`changeHeaderFormat.py`)

**Inputs:** Raw FASTQ paired-end reads (R1, R2)  
**Outputs:** Filtered FASTQ files, QC report

---

### Module 2 — Assembly (`assembly/`)

**Entry:** `assemblyQt.py` → `assembly.py` (`mainAlgorithm()` inside `Toplevel1.__init__`)

**What it does (in order):**
1. Subsamples reads at multiple depths to find optimal coverage
2. Runs SPAdes de novo assembler at each depth
3. Ranks resulting assemblies by N50 (`getBestAssembly.py`)
4. Selects best assembly and proceeds to scaffolding
5. Aligns reads to reference with Bowtie2/BWA
6. Builds reference-guided scaffolds (`scaffold_builder.py` — custom Needleman-Wunsch)
7. Joins scaffolds into a draft genome (`joinScaffolds*.py`)
8. Fills gaps using original reads (`completeGenome*.py`)
9. Calls first consensus (Lofreq / VarScan)
10. Refines and calls second consensus
11. Writes final assembly FASTA + BAM + VCF

**Config file (`assembly.conf`) key parameters:**
```
Project_name, Read1_toAssemble, Read2_toAssemble
Read1_toFill, Read2_toFill
Reads_quality_filter=[yes/no], minQualMean, trimLeft, minLen
Denovo_assembly=[yes/no]
Scaffolding=[yes/no]
First_Consensus_call=[yes/no]
Second_consensus_call=[yes/no]
Refine_assembly=[yes/no]
```

**Inputs:** Filtered FASTQ (R1, R2), optional config file  
**Outputs:** `*_scaffolds.fasta`, `*.bam`, `*.vcf`, coverage plots, N50 plots

---

### Module 3 — Genotyping (`genotyping/`)

**Entry:** `genotypingQt.py` → `genotyping.py`

**What it does:**
- Counts k-mers in the assembled genome using Jellyfish
- Compares k-mer profile against pre-built species/strain databases in `kmerDB/`
- `mainDB_seqs*.txt` — k-mer lists per known strain
- `ambiguousKmers.txt` — k-mers shared across strains (excluded)
- Reports strain identity and confidence score

**Inputs:** Assembled FASTA genome  
**Outputs:** Genotyping report (strain ID, % k-mer match)

---

### Module 4 — SNP Calling (`snpCalling/`)

**Entry:** `snpCallingQt.py` → `snpCalling.py`

**What it does:**
- Aligns reads to final assembly (Bowtie2)
- Calls variants (Lofreq or VarScan)
- Filters VCF with `varscanFilter.py`
- Detects homopolymer runs (`polyAn.py`) and trims poly-N/G/C tails (`trimPolyN.py`)
- Translates SNPs to codon changes
- Builds SNP comparison table (`buildTable.py`)
- Generates heatmap visualizations (`plotHeatmap.py`, Matplotlib)

**Inputs:** Filtered FASTQ reads, assembled FASTA  
**Outputs:** Filtered VCF, SNP table (TSV), heatmap PNG

---

### Module 5 — Annotation (`annotation/`)

**Entry:** `annotationQt.py` → `annotation.py` + `lncRNA_annotation.py`

**What it does:**
- BLASTs assembled genome against `proteinDB/` (pre-built DBs for ~20 HCMV proteins: UL*, RL*, IRS1, TRS1)
- Maps protein hits to genome coordinates
- Annotates long non-coding RNAs (`lncRNA_annotation.py` vs `lncRNAs.fasta`)
- Produces GFF3 annotation file formatted for ENA submission

**Inputs:** Assembled FASTA genome  
**Outputs:** `*.gff3` annotation file

---

### Module 6 — Database Submission (`dbsubmission/`)

**Entry:** `dbsubmissionQt.py` → `dbsubmission.py`

**What it does:**
- Validates assembly and annotation against ENA checklist (`annotationChecklist.txt`)
- Guides user through filling the ENA submission worksheet
- Packages genome FASTA + GFF3 + metadata for ENA upload
- Generates submission-ready files

**Inputs:** Assembled FASTA, GFF3 annotation, user metadata  
**Outputs:** ENA submission package

---

## Data Flow Diagram

```
Raw FASTQ reads (R1, R2)
        │
        ▼
[1] Reads Filtering ──────────────────────── trim-galore, cutadapt, fastuniq
        │ filtered FASTQ
        ▼
[2] Assembly ─────────────────────────────── SPAdes, Bowtie2/BWA, Lofreq/VarScan
        │ scaffolds.fasta + BAM + VCF
        ├──────────────────────────────────→ [3] Genotyping (FASTA in → strain report)
        │                                        jellyfish + kmerDB
        ├──────────────────────────────────→ [4] SNP Calling (FASTQ + FASTA → VCF + heatmap)
        │                                        Bowtie2, Lofreq/VarScan, Matplotlib
        ├──────────────────────────────────→ [5] Annotation (FASTA → GFF3)
        │                                        BLAST + proteinDB
        ▼
[6] DB Submission ──────────────────────── (FASTA + GFF3 + metadata → ENA package)
```

Modules 3–5 can run in any order after Module 2 completes. All inter-module communication is via files.

---

## Key Patterns & Conventions

### GUI Pattern (every module)

Every module follows this identical pattern:

```python
# *Qt.py files
class Toplevel1:
    def __init__(self, top=None):
        # All UI setup AND all pipeline logic live here
        self.button.configure(command=self.mainAlgorithm)

    def mainAlgorithm(self):
        # Reads form fields, builds shell command strings, calls os.system()
        os.system("spades.py -1 " + self.read1 + " -2 " + self.read2 + " ...")

def vp_start_gui():
    root = tk.Tk()
    Toplevel1(root)
    root.mainloop()
```

**Critical:** All logic is embedded inside `__init__` or methods of the single `Toplevel1` class. There is no separation of GUI from business logic.

### External Tool Invocation

All external bioinformatics tools are called via:
```python
os.system("toolname arg1 arg2 ...")   # return code ignored
```
- Return codes are never checked
- User input is concatenated directly into shell strings (command injection risk)
- The conda environment binary path is prepended to every tool call using `installDir`

### Configuration Parsing

Assembly config files are plain `key=value` INI files parsed manually:
```python
for line in open(configFile):
    if "Project_name" in line:
        projectName = line.split("=")[1].strip()
```

### Shared Utilities

`src/scripts/utils/biomodule.py` provides:
- `reverseComplement(seq)` — BioPython-based reverse complement
- `ambiguityCode(bases)` — IUPAC ambiguity code lookup

All other utilities in module-level `utils/` subdirectories are standalone scripts called via `os.system()` with `sys.argv` argument passing (not imported as Python modules).

---

## Installation & Runtime Environment

**Installation (`install.sh`):**
1. Checks for existing Miniconda3; installs if absent (from bundled `.sh` in `src/`)
2. Creates conda env with pinned versions of all bioinformatics tools
3. Creates a second conda env (Python 2) solely for RAGOUT scaffolding tool
4. Rewrites shebang line of `GRACy.py` to point to the local conda Python
5. Sets `INSTALLATION_DIRECTORY` env var

**Conda environments:**
- `gracy_env` (Python 3) — all tools except RAGOUT
- `gracy_env2` (Python 2, EOL) — RAGOUT only

**Runtime:**
```bash
./GRACy.py                     # Tkinter main window
# Each module button spawns:
python <installDir>/src/scripts/<module>/<module>Qt.py <installDir>
```

---

## Reference Data

| Location | Contents | Used By |
|----------|---------|---------|
| `data/merlinReference/hcmv_genome.fasta` | HCMV Merlin reference genome | Assembly (scaffolding) |
| `data/merlinReference/*.bt2` | Bowtie2 index | Assembly |
| `data/merlinReference/hcmv_genome.fasta.*` | BLAST index | Assembly |
| `data/merlinReference/merlinGenome_*.txt` | Segment annotations | Assembly, Annotation |
| `src/scripts/annotation/proteinDB/` | BLAST DBs for ~20 HCMV proteins | Annotation |
| `src/scripts/genotyping/kmerDB/` | K-mer databases for strain ID | Genotyping |
| `src/scripts/genotyping/fastaFiles/` | Reference sequences per species | Genotyping |

---

## Known Issues & Technical Debt

| Issue | Location | Severity |
|-------|---------|---------|
| Command injection via `os.system()` with unsanitized user input | All `*Qt.py` files | High |
| Return codes from all `os.system()` calls silently ignored | All modules | High |
| All logic embedded in `Toplevel1.__init__` — untestable, not headless | All `*Qt.py` | High |
| `assembly.py` is a single 1,133-line method | `assembly/assembly.py` | Medium |
| Python 2 EOL conda env (RAGOUT now supports Python 3) | `install.sh` | Medium |
| Miniconda installers committed to repo (756 MB bloat) | `src/Miniconda*.sh` | Medium |
| Hardcoded developer HPC path in original shebang (rewritten at install) | `GRACy.py` | Low |
| macOS AppleDouble `._*.py` files committed | Throughout `src/` | Low |
| No test suite; `testDataset/` is empty | Repo root | Medium |
| Linux-only despite partial `sys.platform == "win32"` checks | Throughout | Low |

---

## Quick Reference: Entry Points per Task

| Task | File to edit |
|------|-------------|
| Change main window layout | `src/.GRACy_main.py` |
| Add a new pipeline module | `src/.GRACy_main.py` (button) + new `<module>/<module>Qt.py` |
| Fix assembly pipeline logic | `src/scripts/assembly/assembly.py` |
| Change scaffolding algorithm | `src/scripts/assembly/utils/scaffold_builder.py` |
| Add a new reference genome | `data/` (add FASTA + build Bowtie2/BLAST indices) |
| Change annotation proteins | `src/scripts/annotation/proteinDB/` |
| Update k-mer strain database | `src/scripts/genotyping/kmerDB/` |
| Change tool versions | `install.sh` (conda install pinned versions) |
| Fix SNP heatmap | `src/scripts/snpCalling/utils/plotHeatmap.py` |
