#!/bin/bash
# verify_install.sh — full-chain verification of the Miniconda3 toolchain install.
#
# Reproduces the Miniconda3 section of install.sh (same channels, version pins, and
# order) into a THROWAWAY conda prefix, then reports per-package pass/fail and whether
# any Anaconda Terms-of-Service gate fired. This is the manual, heavy counterpart to the
# unittest guard in tests/test_install_miniconda_pin.py: the unittest proves the script
# still *pins* a py37 build; this proves the pinned build actually *installs the whole
# toolchain* on a clean machine. Guards ADR-0001.
#
# Usage:   bash tests/harness/verify_install.sh [workdir]
#   workdir  optional; defaults to a mktemp dir. Set KEEP=1 to keep it for inspection.
# Runs for many minutes and downloads ~100MB + a few GB of packages. Network required.
#
# It reads the pinned installer name FROM install.sh so it can never test a different
# version than the script ships. The package list below mirrors install.sh's Miniconda3
# section — keep the two in sync if that section changes.
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INST=$(grep -oE 'Miniconda3-py37[^"]+\.sh' "$REPO/install.sh" | head -1)
[ -n "$INST" ] || { echo "FATAL: could not read pinned Miniconda3 installer from install.sh"; exit 2; }

WORKDIR="${1:-$(mktemp -d "${TMPDIR:-/tmp}/gracy-install-verify.XXXXXX")}"
mkdir -p "$WORKDIR"
PREFIX="$WORKDIR/conda"
LOG="$WORKDIR/install.log"; : > "$LOG"
CONDA="$PREFIX/bin/conda"
pass=0; fail=0; tos=0

echo "installer : $INST"
echo "workdir   : $WORKDIR"
echo "downloading + installing Miniconda3 (throwaway) ..."
[ -f "$WORKDIR/$INST" ] || wget -q "https://repo.anaconda.com/miniconda/$INST" -O "$WORKDIR/$INST"
rm -rf "$PREFIX"
bash "$WORKDIR/$INST" -b -p "$PREFIX" >> "$LOG" 2>&1
$CONDA config --set notify_outdated_conda false >> "$LOG" 2>&1
echo "base python: $($PREFIX/bin/python --version 2>&1)   conda: $($CONDA --version 2>&1)"
echo

check () {  # check <name> <conda install args...>
  local name="$1"; shift
  local out; out=$($CONDA install "$@" 2>&1); echo "$out" >> "$LOG"
  local g="no"
  echo "$out" | grep -qi "CondaToSNonInteractiveError\|Terms of Service have not been accepted" && { g="TOS-GATE"; tos=$((tos+1)); }
  if $CONDA list 2>/dev/null | grep -Fq "$name"; then
    printf "  PASS  %-22s (tos=%s)\n" "$name" "$g"; pass=$((pass+1))
  else
    printf "  FAIL  %-22s (tos=%s)\n" "$name" "$g"; fail=$((fail+1))
  fi
}

check pillow      -c anaconda -y pillow
check numpy       -c anaconda -y numpy
$PREFIX/bin/pip install matplotlib >> "$LOG" 2>&1; echo "  (matplotlib via pip)"
$CONDA config --add channels bioconda >> "$LOG" 2>&1
check trim-galore -y trim-galore
check bowtie2     -c bioconda -y bowtie2=2.3.5.1
$CONDA install -y tbb=2020.2 >> "$LOG" 2>&1
check bam2fastq   -c yuxiang -y bam2fastq=1.1.0
check fastuniq    -c bioconda -y fastuniq=1.1
check cutadapt    -c bioconda -y cutadapt=2.6
check pypdf2      -c conda-forge -y pypdf2=1.26.0
check reportlab   -c anaconda -y reportlab=3.5.9
check biopython   -c bioconda -y biopython=1.76
check jellyfish   -c bioconda -y jellyfish=2.2.10
check bwa         -c bioconda -y bwa=0.7.17
check prinseq     -c bioconda -y prinseq=0.20.4
check khmer       -c bioconda -y khmer=3.0.0
check seqtk       -c bioconda -y seqtk=1.3
check spades      -c bioconda -y spades=3.12
check picard      -c bioconda -y picard=2.21
check lastz       -c bioconda -y lastz=1.0.4
check perl-perl4-corelibs -c bioconda -y perl-perl4-corelibs
check blast       -c bioconda -y blast=2.9.0
check cd-hit      -c bioconda -y cd-hit=4.8.1
check cap3        -c bioconda -y cap3
check bedtools    -c bioconda -y bedtools=2.29.2
check fastx_toolkit -c bioconda -y fastx_toolkit=0.0.14
check blat        -c bioconda -y blat=36
check exonerate   -c bioconda -y exonerate=2.4
check pyqt        -c anaconda -y pyqt=5.9.2
check varscan     -c bioconda -y varscan=2.4.4
check tabix       -c bioconda -y tabix
check samtools    -c bioconda -y samtools=1.3.1

echo
echo "SUMMARY: PASS=$pass FAIL=$fail TOS_GATES=$tos   (detail: $LOG)"
if [ "${KEEP:-0}" = "1" ]; then
  echo "workdir kept at $WORKDIR"
else
  rm -rf "$PREFIX" "$WORKDIR/$INST"
  echo "cleaned throwaway env (log kept at $LOG; rm -rf $WORKDIR to remove)"
fi
[ "$fail" -eq 0 ] && [ "$tos" -eq 0 ]  # exit non-zero if anything failed or a ToS gate fired
