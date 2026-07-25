#!/bin/bash
# verify_toolchain.sh — does each installed tool the pipeline invokes actually RUN here?
#
# Companion to verify_install.sh. That one proves the toolchain *installs*; this one proves
# the installed tools *load and run* on this machine. It exists because "installed" is not
# "runnable": the #11 smoke test found tools that install fine but then fail at run time —
#   * khmer   -> ImportError: libgomp.so.1 missing        (fixed: install libgomp, see #11)
#   * SPAdes  -> spades-core/spades-hammer segfault (#30)  on WSL2 / modern glibc
#   * varscan -> bare `java` not on PATH -> silent no-op (#33)
#
# For every tool the pipeline shells out to (the src/conda[2]/bin/<tool> calls in src/scripts),
# it runs a minimal load-level invocation (--version/--help, or the interpreter for a script)
# and classifies the result. Load-level only: it catches segfaults, missing shared libraries,
# missing binaries, and broken wrappers — NOT data-dependent runtime bugs. No data, no network,
# runs in seconds.
#
# Usage:   bash tests/harness/verify_toolchain.sh
# Exit:    0 if every tool loaded; non-zero if any SEGFAULT / MISSING-LIB / MISSING-BIN /
#          BROKEN-WRAPPER was seen. A "usage" non-zero exit (bwa, seqtk, cap3 with no args)
#          counts as loaded — the point is whether the binary runs, not its argument parsing.
set -u
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
C="$R/src/conda/bin"
C2="$R/src/conda2/bin"
PY="$C/python"; PY2="$C2/python"; PERL="$C/perl"
seg=0; lib=0; missbin=0; wrap=0; ok=0

run () {  # run <env> <name> <cmd...>   — <cmd> is exactly how to load the tool
  local env="$1" name="$2"; shift 2
  if [ ! -e "$1" ]; then printf "  %-7s %-20s MISSING-BIN\n" "$env" "$name"; missbin=$((missbin+1)); return; fi
  local out rc
  out=$(timeout 90 "$@" </dev/null 2>&1); rc=$?
  if echo "$out" | grep -qiE "segmentation fault|core dumped" || [ "$rc" = 139 ] || [ "$rc" = 134 ]; then
    printf "  %-7s %-20s SEGFAULT (rc=%s)\n" "$env" "$name" "$rc"; seg=$((seg+1))
  elif echo "$out" | grep -qiE "cannot open shared object|error while loading shared librar|ImportError|ModuleNotFoundError"; then
    printf "  %-7s %-20s MISSING-LIB: %s\n" "$env" "$name" "$(echo "$out" | grep -ioE 'lib[^ ]*: cannot open shared object|No module named [^ ]+' | head -1)"; lib=$((lib+1))
  elif echo "$out" | grep -qiE "command not found"; then
    # A wrapper script exec'ing a tool that isn't on PATH (e.g. varscan -> bare `java`).
    # NB: a benign "setlocale: ... No such file or directory" warning is NOT this.
    printf "  %-7s %-20s BROKEN-WRAPPER: %s\n" "$env" "$name" "$(echo "$out" | grep -iE 'command not found' | head -1 | sed 's/^[^:]*: *//')"; wrap=$((wrap+1))
  else
    printf "  %-7s %-20s ok\n" "$env" "$name"; ok=$((ok+1))
  fi
}

echo "toolchain: $C"
echo "=== conda (main env) ==="
run conda java          "$C/java" -version
run conda bowtie2       "$C/bowtie2" --version
run conda bowtie2-build "$PY" "$C/bowtie2-build" --version   # #!/usr/bin/env python wrapper
run conda bwa           "$C/bwa"
run conda samtools      "$C/samtools" --version
run conda bedtools      "$C/bedtools" --version
run conda bgzip         "$C/bgzip" --version
run conda tabix         "$C/tabix" --version
run conda blastn        "$C/blastn" -version
run conda tblastn       "$C/tblastn" -version
run conda makeblastdb   "$C/makeblastdb" -version
run conda blat          "$C/blat"
run conda cap3          "$C/cap3"
run conda cd-hit-est    "$C/cd-hit-est" -h
run conda cutadapt      "$C/cutadapt" --version
run conda exonerate     "$C/exonerate" --version
run conda fastq_to_fasta "$C/fastq_to_fasta" -h
run conda fastuniq      "$C/fastuniq"
run conda jellyfish     "$C/jellyfish" --version
run conda lastz         "$C/lastz" --version
run conda seqtk         "$C/seqtk"
run conda bam2fastq     "$C/bam2fastq" --version
run conda picard        "$C/picard" SortVcf --version
run conda varscan       "$C/varscan"
run conda trim_galore   "$PERL" "$C/trim_galore" --version
run conda prinseq       "$PERL" "$C/prinseq-lite.pl" --version
run conda interleave    "$PY" "$C/interleave-reads.py" --help
run conda normalize     "$PY" "$C/normalize-by-median.py" --help
run conda spades.py     "$PY" "$C/spades.py" --version              # wrapper only
run conda spades-core   "$C"/../share/spades-*/bin/spades-core      # the binary that runs assembly

echo "=== conda2 (Python-2 / Ragout env) ==="
run conda2 bcftools     "$C2/bcftools" --version
run conda2 lofreq       "$C2/lofreq" version
run conda2 nucmer       "$C2/nucmer" --version
run conda2 show-coords  "$C2/show-coords"
run conda2 ragout       "$PY2" "$C2/ragout" --help

echo
echo "SUMMARY: ok=$ok  SEGFAULT=$seg  MISSING-LIB=$lib  MISSING-BIN=$missbin  BROKEN-WRAPPER=$wrap"
echo "(known: spades-core SEGFAULT -> #30; varscan BROKEN-WRAPPER without PATH java -> #33)"
[ $((seg+lib+missbin+wrap)) -eq 0 ]
