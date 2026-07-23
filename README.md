# GRACy — Genome Research Assistant for CytomegaloVirus

GRACy is a desktop GUI pipeline for end-to-end HCMV (Human Cytomegalovirus) genome assembly and analysis. It provides a point-and-click interface wrapping ~25 bioinformatics command-line tools, targeting wet-lab scientists who are not command-line proficient.

This is a fork of the [original GRACy by salvocamiolo](https://github.com/salvocamiolo/GRACy) with bugfixes and updates.

---

## Requirements

- Linux (x86_64)
- ~10 GB disk space for conda environments
- Internet connection for the initial install

---

## Installation

```bash
bash install.sh
```

This runs once. It installs two bundled Conda environments (`src/conda/` and `src/conda2/`) containing all required tools. After installation, `GRACy.py` is updated with the correct paths for your system.

---

## Running

```bash
./GRACy.py
```

This opens the main launcher window with six module buttons.

---

## Pipeline Modules

Run modules in order, or independently as needed. Each module is a separate window.

| # | Module | Input | Output |
|---|--------|-------|--------|
| 1 | **Reads Filtering** | Raw paired-end FASTQ (R1, R2) | Quality-filtered FASTQ |
| 2 | **Assembly** | Filtered FASTQ + `.conf` config file | `*_genome.fasta`, BAM, VCF |
| 3 | **Genotyping** | Paired-end FASTQ | Strain identity report |
| 4 | **SNP Calling** | FASTQ + assembled FASTA | Filtered VCF, SNP table, heatmap |
| 5 | **Annotation** | Assembled FASTA | GFF3 annotation file |
| 6 | **DB Submission** | FASTA + GFF3 + metadata | ENA submission package |

### Assembly config file

Module 2 reads a tab-delimited `.conf` file. Use `data/assembly.conf` as a template. Key fields:

```
Project_name        <name>
Read1_toAssemble    <path to R1 FASTQ>
Read2_toAssemble    <path to R2 FASTQ>
Read1_toFill        <path to R1 FASTQ>
Read2_toFill        <path to R2 FASTQ>
Reads_quality_filter    yes
Denovo_assembly         yes
Scaffolding             yes
First_Consensus_call    yes
Second_consensus_call   yes
Refine_assembly         yes
```

A script to auto-generate config files for batch runs is available at: https://github.com/Kosennai/GRACy-Auto-Config-Maker

---

## Reference Data

The `data/merlinReference/` directory contains the HCMV Merlin strain reference genome (NC_006273.2) and pre-built Bowtie2 and BLAST indices used for scaffolding. This is the default reference for HCMV workflows.

---

## Test Dataset

A small test dataset (synthetic HCMV reads) is in `testDataset/reads/`. Use with `data/assembly.conf` as a quick end-to-end check after installation.

---

## Known Issues

- Paths with spaces in project names or file paths will cause pipeline failures (shell quoting issue)
- The Python 2 conda environment (`src/conda2/`) is retained for Ragout compatibility; this may be removed in a future update
- No Windows or macOS support

---

## License

GPL-3.0 — see `license.txt`.
