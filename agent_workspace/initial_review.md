# GRACy — Initial Code Review

**Date:** 2026-05-20  
**Repo:** https://github.com/RichStanton/GRACy

---

## What it is

A bioinformatics GUI tool for analysing Human Cytomegalovirus (HCMV) genome sequences. It wraps a pipeline of ~20 command-line tools (bowtie2, samtools, SPAdes, GATK, lofreq, etc.) in a Tkinter desktop app covering:

**Read QC → De novo assembly → Scaffolding → Genotyping → SNP calling → Annotation → ENA database submission**

**Tech stack:** Python 2/3 (dual-conda approach), Tkinter GUI, bioconda toolchain, Linux/HPC-only.

---

## Key Strengths

- Covers a genuinely complex end-to-end pipeline in a GUI wrapper — real utility for wet-lab scientists who don't want to use the command line
- Good modular structure: separate scripts per pipeline stage
- Versioned release tags (v0.1 → v0.7) suggest it has been iterated over time and actually used in practice

---

## Concerns

### Critical / Blocking

**1. Hardcoded absolute path from the developer's HPC**

`GRACy.py` line 1 has `#!/home3/scc20x/Software/mySoftware/GRACy/src/conda/bin/python` baked in as the shebang. This is rewritten at install time by `install.sh` lines 1–5, but the file committed to the repo is unusable as-is. Anyone cloning without running the install script first will get a broken launcher.

**2. Command injection via `os.system()` with unsanitised user input**

For example, `assembly.py` lines 91–93:
```python
os.system("mkdir -p "+projectName)
```
`projectName` comes directly from a user-supplied config file. A value like `; rm -rf /` would be executed. This pattern is repeated throughout every module. The fix is to replace `os.system()` with `subprocess.run([...], shell=False)` using argument lists.

**3. No error handling on any `os.system()` calls**

Return codes are silently ignored everywhere. If bowtie2 fails, the pipeline continues as if it succeeded. This could produce silently wrong scientific results with no indication of failure.

**4. Linux-only with no guardrail**

All paths use forward slashes and the bioinformatics tools (prinseq, lofreq, etc.) are Linux binaries. The Tkinter code checks `sys.platform == "win32"` for styling (suggesting someone considered other platforms), but the tool cannot actually run on Windows or macOS.

---

### Moderate

**5. Requires two separate Conda environments (Python 2 and Python 3)**

`install.sh` installs both `Miniconda2` and `Miniconda3` side by side. The Python 2 environment exists solely to run `ragout` (a scaffolding tool). Python 2 has been end-of-life since January 2020, and ragout now supports Python 3 — this could be collapsed into one environment.

**6. Miniconda installers bundled in the repo**

`src/Miniconda2-latest-Linux-x86_64.sh` and `src/Miniconda3-latest-Linux-x86_64.sh` are large binaries committed to git. This is why the repo is ~331 MB. They should be downloaded at install time, not versioned.

**7. All pipeline logic nested inside the Tkinter `__init__` constructor**

`assembly.py` is a 1,134-line `__init__` method where the entire assembly algorithm lives as a nested function. This makes the logic impossible to test, reuse, or run headlessly (e.g. from a script or HPC job scheduler).

**8. Large amounts of dead / commented-out code**

Large blocks of `#os.system(...)` calls are commented out across multiple files (e.g. `assembly.py` lines 260–266), suggesting in-progress work or abandoned alternatives. Additionally, Mac AppleDouble `._*.py` hidden files are committed alongside every source file.

**9. Typos in user-facing messages and log output**

| Location | Typo |
|---|---|
| `assembly.py:406` | "Adding gorup names" |
| `assembly.py:464` | "Adding gorup names" (again) |
| `assembly.py:247` | "Scaffold Oriantation" (comment) |
| `assembly.py:584` | "First consensus calline ended" (log write) |

---

### Minor

- **No tests** — no test files anywhere in the repo, no CI configuration
- **README is two sentences** and links to the original author's repo rather than explaining this fork
- **Mac junk files committed** — `.DS_Store` and `._` AppleDouble files are checked in; `.gitignore` only excludes the conda directories

---

## Quick Wins

| Fix | Effort |
|---|---|
| Add `.DS_Store`, `._*` and the Miniconda `.sh` files to `.gitignore` and remove from repo history | 15 mins |
| Delete the `._*.py` AppleDouble files | 5 mins |
| Remove commented-out dead code | 30 mins |
| Fix the four typos in log/UI messages | 5 mins |
| Write a proper README with install instructions and usage for this fork | 1 hour |
| Replace `os.system()` with `subprocess.run()` and check return codes | Medium — affects all modules |

---

## Summary

This is functioning research software — not production code, but that's expected for academic bioinformatics tools. The two biggest real risks are:

1. **Command injection** — fine in a trusted HPC environment with known inputs, but a concern if the tool is ever distributed more widely
2. **Silent pipeline failure** — `os.system()` return codes are never checked, so a failed alignment step would not be reported and downstream results could be wrong without any warning

For a lab tool used by a small trusted team, it is workable. It would need significant refactoring before broader public distribution.
