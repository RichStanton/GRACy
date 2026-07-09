# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What GRACy Is

GRACy is a bioinformatics GUI pipeline for viral genome assembly and analysis, primarily targeting HCMV (Human Cytomegalovirus). It wraps a collection of bioinformatics tools (SPAdes, BWA, Bowtie2, Samtools, BLAST, VarScan, LoFreq, etc.) behind Tkinter and PyQt5 GUIs, providing a point-and-click interface for sequencing analysis workflows.

## Installation and Running

Install (only needed once, sets up two bundled Conda environments):
```bash
bash install.sh
```

Run the main launcher:
```bash
./GRACy.py
```

`install.sh` generates `GRACy.py` by prepending a shebang (`src/conda/bin/python`) and `installationDirectory` variable to `src/.GRACy_main.py`. After re-running install on a new machine the absolute paths in `GRACy.py` will be updated automatically — do not edit the shebang or `installationDirectory` line directly.

## Claude Code Setup (for contributors)

This project uses the [Compound Engineering plugin](https://github.com/EveryInc/compound-engineering-plugin) for structured AI-assisted development. Install it once after cloning:

```bash
claude /plugin marketplace add https://github.com/EveryInc/compound-engineering-plugin
```

Then run `/ce-setup` inside Claude Code to bootstrap your local environment. The plugin is enabled for this project via `.claude/settings.json` (committed). Your machine-specific permissions live in `.claude/settings.local.json` (gitignored).

## Testing and Linting

There are no automated tests. Linting is configured in `pyproject.toml` (Ruff) and `.bandit` (Bandit security scanner). Run with:
```bash
~/.local/bin/ruff check src/
~/.local/bin/bandit -r src/ -f txt
```

## Architecture

### Two-Environment Design

The pipeline relies on two bundled Conda environments due to Python 2/3 incompatibility of some tools:

- `src/conda/` — Python 3 environment: main tools (SPAdes, BWA, Bowtie2, Samtools, BLAST, VarScan, Trimgalore, PRINSEQ, CD-HIT, Jellyfish, BLAT, Exonerate, PyQt5, Biopython, etc.)
- `src/conda2/` — Python 2 environment: Ragout (scaffolding), MUMmer, BCFtools, LoFreq

All tool invocations use absolute paths through `installationDirectory`, e.g.:
```python
os.system(installationDirectory + "src/conda/bin/bowtie2 ...")
```

### Main Launcher → Module Pattern

`GRACy.py` (Tkinter window) launches each analysis module as a separate subprocess:
```python
os.system(installationDirectory + "src/conda/bin/python " + installationDirectory + "src/scripts/<module>/<module>Qt.py " + installationDirectory + " &")
```

Each module receives `installationDirectory` as `sys.argv[1]`.

### Module Structure

Each module under `src/scripts/` follows the same pattern:

| File | Purpose |
|---|---|
| `<module>.py` | Tkinter UI + core processing logic |
| `<module>Qt.py` | PyQt5 alternative UI for the same module |
| `utils/` | Helper scripts called via `os.system()` |

The modules are:
- `readsFiltering/` — quality filtering and trimming (PRINSEQ, TrimGalore, Cutadapt)
- `assembly/` — de novo genome assembly (SPAdes), scaffolding (Ragout/MUMmer), gap filling, consensus calling
- `genotyping/` — genotyping via BWA/Bowtie2 alignment and VarScan/LoFreq variant calling
- `annotation/` — gene annotation using BLAST against `src/scripts/annotation/proteinDB/` FASTA databases
- `snpCalling/` — SNP calling and heatmap visualisation
- `dbsubmission/` — ENA database submission preparation

### Assembly Pipeline Output Directories

The assembly module creates numbered subdirectories within a project folder:
1. `1_cleanReads/` — quality-filtered reads
2. `2_spadesAssembly/` — SPAdes scaffolds
3. `3_scaffoldsOrientation/` — Ragout-oriented scaffolds
4. Further stages for gap filling, consensus calling, and refinement

### Configuration Files

Assembly jobs are driven by tab-delimited `.conf` files (see `data/assembly.conf` for the template). The file is parsed line-by-line in strict order — field order matters. A text file listing paths to multiple `.conf` files can be passed to batch-process samples.

### Reference Data

`data/merlinReference/` contains HCMV Merlin strain reference sequences used as scaffolding/alignment templates. These are the expected reference inputs for the default HCMV workflow.

### Agent Workspace

`agent_workspace/` is a dedicated directory for Claude Code working files and artefacts. It is tracked in version control. Read `agent_workspace/README.md` at the start of every session for current project phase and context.
