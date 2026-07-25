#!/usr/bin/env python
"""smoke_assembly.py — end-to-end smoke test of the GRACy assembly pipeline (issue #11).

Runs the *real* current pipeline on the committed `testDataset/` reads and checks that it
completes and produces a non-empty, plausible HCMV genome. This is the safety net the
structural refactors (#12 runner, #14 headless seam, #16 subprocess) lean on: once a
maintainer blesses a golden output, this harness turns a behaviour change into a red test.

Why it drives the Qt widget: today the assembly pipeline has *no* headless entry point — the
whole orchestration lives in `Ui_Form.performAssembly`, and `installationDirectory` is a
module global set only inside `if __name__ == "__main__"`. So the only way to exercise the
actual production code path is to construct the widget offscreen and call `performAssembly()`.
Extracting a real `assemble(config, log=cb)` is issue #14 — which is *blocked by this test*,
because this golden is what proves that refactor preserved behaviour. When #14 lands, point
`run_pipeline()` at `assemble()` instead; the golden should not move.

Heavy + manual (like tests/harness/verify_install.sh): a full run shells out to bowtie2,
SPAdes, samtools, picard, bcftools on ~130 MB of reads and takes many minutes. It needs the
bundled toolchain (`src/conda` + `src/conda2`) installed. It is NOT part of `unittest
discover`; the fast guard `tests/test_smoke_assembly_harness.py` unit-tests the pure checks
below without running the pipeline.

Usage:
    # Full run (needs the toolchain); prints a fingerprint to bless as the golden:
    bash tests/harness/smoke_assembly.sh
    # or directly:
    src/conda/bin/python tests/harness/smoke_assembly.py [--run-dir DIR] [--keep] [--golden FILE]

    # Validate the plausibility/fingerprint checks alone, no toolchain, in seconds:
    python3 tests/harness/smoke_assembly.py --check-only

Exit codes: 0 = pipeline completed and the genome is plausible (and matches the golden if one
was given); 1 = missing/empty/implausible genome or golden mismatch; 2 = harness/setup error.
"""
import argparse
import hashlib
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ASSEMBLY_PY = REPO / "src" / "scripts" / "assembly" / "assemblyQt.py"
CONF_TEMPLATE = REPO / "tests" / "fixtures" / "smoke_assembly.conf.template"
READS_DIR = REPO / "testDataset" / "reads"
DEFAULT_RESULTS = REPO / "tests" / "_results"        # gitignored throwaway
PROJECT_NAME = "merlin"                               # must match the conf's Project_name

# --- Plausibility bounds -----------------------------------------------------------------
# HCMV (Merlin) is ~235,646 bp. These are deliberately GENEROUS smoke bounds: their only job
# is to reject an empty / truncated / garbage genome. Exact regression power comes from the
# blessed golden, not from these. A maintainer should tighten them once the real output
# length from a blessed run is known.
MIN_PLAUSIBLE_LEN = 100_000
MAX_PLAUSIBLE_LEN = 260_000
MAX_N_FRACTION = 0.5
DNA_ALPHABET = set("ACGTNacgtn")


# --- Pure checks (no PyQt / no toolchain — unit-tested by the fast guard) -----------------
def read_fasta_seq(path):
    """Concatenated sequence of every record in a FASTA file (newlines/headers stripped)."""
    seq = []
    with open(path) as fh:
        for line in fh:
            if not line.startswith(">"):
                seq.append(line.strip())
    return "".join(seq)


def fingerprint(seq):
    """Stable identity of a genome: length, N content, and a sha256 of the uppercased bases."""
    upper = seq.upper()
    n_count = upper.count("N")
    return {
        "length": len(seq),
        "n_count": n_count,
        "n_fraction": (n_count / len(seq)) if seq else 0.0,
        "sha256": hashlib.sha256(upper.encode()).hexdigest(),
    }


def check_plausible(seq):
    """Return a list of human-readable problems; empty means the genome looks like a genome."""
    problems = []
    if len(seq) == 0:
        return ["genome is empty"]
    if len(seq) < MIN_PLAUSIBLE_LEN:
        problems.append("genome too short: %d bp (< %d)" % (len(seq), MIN_PLAUSIBLE_LEN))
    if len(seq) > MAX_PLAUSIBLE_LEN:
        problems.append("genome too long: %d bp (> %d)" % (len(seq), MAX_PLAUSIBLE_LEN))
    stray = sorted(set(seq) - DNA_ALPHABET)
    if stray:
        problems.append("non-DNA characters present: %r" % stray)
    fp = fingerprint(seq)
    if fp["n_fraction"] > MAX_N_FRACTION:
        problems.append("too many Ns: %.1f%% (> %.0f%%)"
                        % (fp["n_fraction"] * 100, MAX_N_FRACTION * 100))
    return problems


def format_fingerprint(fp):
    return ("length=%d bp  N=%d (%.2f%%)  sha256=%s"
            % (fp["length"], fp["n_count"], fp["n_fraction"] * 100, fp["sha256"]))


def compare_to_golden(seq, golden_path):
    """Return (ok, message) comparing seq's sha256 to a blessed golden fingerprint file.

    The golden file is a one-line fingerprint (see format_fingerprint) written by a maintainer
    from a blessed run. We compare the sha256 token so trivial reformatting can't weaken it.
    """
    golden_text = Path(golden_path).read_text().strip()
    token = "sha256="
    if token not in golden_text:
        return False, "golden file %s has no sha256= token: %r" % (golden_path, golden_text)
    golden_sha = golden_text.split(token, 1)[1].split()[0]
    actual_sha = fingerprint(seq)["sha256"]
    if actual_sha == golden_sha:
        return True, "genome matches golden (sha256=%s)" % actual_sha
    return False, "genome DIFFERS from golden\n  golden: %s\n  actual: %s" % (golden_sha, actual_sha)


# --- Heavy driver (needs PyQt + the toolchain) -------------------------------------------
def _load_assembly_module(installation_dir):
    """Import assemblyQt.py and inject the `installationDirectory` module global it relies on."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("assemblyQt", str(ASSEMBLY_PY))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # performAssembly()/bowtiePE() read `installationDirectory` as a free (module-global)
    # name; it only exists when the file is run as __main__. Supply it so the widget's tool
    # calls resolve `<repo>/src/conda/bin/...`. This coupling is exactly what #14 removes.
    mod.installationDirectory = installation_dir
    return mod


def render_conf(run_dir):
    """Write a run-local .conf from the fixture template, pointing at the testDataset reads."""
    text = CONF_TEMPLATE.read_text().replace("@READS@", str(READS_DIR))
    conf_path = run_dir / (PROJECT_NAME + ".conf")
    conf_path.write_text(text)
    return conf_path


def run_pipeline(run_dir):
    """Drive the real assembly pipeline headless and return the produced genome's sequence.

    Returns the concatenated genome sequence (str). Raises RuntimeError if the pipeline did
    not produce the expected `<project>_genome.fasta`.
    """
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # no display on HPC/CI
    mod = _load_assembly_module(str(REPO) + "/")

    conf_path = render_conf(run_dir)
    prev_cwd = os.getcwd()
    try:
        app = mod.QtWidgets.QApplication.instance() or mod.QtWidgets.QApplication([])
        form = mod.QtWidgets.QWidget()
        ui = mod.Ui_Form()
        ui.setupUi(form, str(REPO) + "/")
        # Inject what the GUI would have gathered from user clicks.
        ui.confFiles = [str(conf_path)]
        ui.selectedFilesArea.setPlainText(conf_path.name)   # non-empty → passes the input guard
        ui.numThreadsCombo.setCurrentText("4")
        ui.memoryCombo.setCurrentText("8")
        ui.intermediateFilesCombo.setCurrentText("No")
        try:
            ui.performAssembly()   # blocking; shells out to the whole toolchain
        except SystemExit:
            # performAssembly calls the builtin exit() when an internal stage fails (e.g.
            # "Something went wrong with the assembly. Now exiting......"). That raises
            # SystemExit, which must NOT read as success — fall through to the genome-existence
            # check below, which turns a missing genome into a hard failure (exit 1).
            pass
        app.processEvents()
    finally:
        os.chdir(prev_cwd)

    # performAssembly copies the final consensus to <workingDirectory>/<project>_genome.fasta,
    # where workingDirectory is the directory holding the conf (our run_dir).
    genome = run_dir / (PROJECT_NAME + "_genome.fasta")
    if not genome.exists():
        raise RuntimeError(
            "pipeline finished but %s was not produced — a stage failed silently "
            "(see logFile.log under %s)" % (genome, run_dir / PROJECT_NAME))
    return read_fasta_seq(genome)


# --- CLI ---------------------------------------------------------------------------------
def _self_check():
    """Exercise the pure checks on synthetic genomes — proves the harness's own logic without
    needing the toolchain. Mirrors the fast unittest guard; handy as a standalone sanity run."""
    good = "ACGT" * (MIN_PLAUSIBLE_LEN // 4 + 10)
    assert check_plausible(good) == [], "a plausible genome must pass"
    assert check_plausible("") == ["genome is empty"]
    assert check_plausible("ACGTX" * 40000), "stray characters must be rejected"
    assert check_plausible("ACGT" * 10), "a tiny genome must be rejected as too short"
    assert fingerprint("ACGT")["sha256"] == fingerprint("acgt")["sha256"], "case-insensitive"
    print("self-check OK — plausibility and fingerprint logic behave")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check-only", action="store_true",
                        help="validate the plausibility/fingerprint logic and exit (no pipeline)")
    parser.add_argument("--run-dir", type=Path, default=None,
                        help="working directory for the run (default: a fresh dir under tests/_results)")
    parser.add_argument("--golden", type=Path, default=None,
                        help="a blessed fingerprint file to compare against (regression mode)")
    parser.add_argument("--keep", action="store_true",
                        help="keep the run directory (default: kept anyway; reserved for future cleanup)")
    args = parser.parse_args(argv)

    if args.check_only:
        return _self_check()

    if not READS_DIR.is_dir():
        print("FATAL: testDataset reads not found at %s" % READS_DIR, file=sys.stderr)
        return 2

    run_dir = args.run_dir or (DEFAULT_RESULTS / "smoke_assembly")
    run_dir.mkdir(parents=True, exist_ok=True)
    print("run dir   : %s" % run_dir)
    print("reads     : %s" % READS_DIR)
    print("running the assembly pipeline (this takes several minutes)...", flush=True)

    try:
        seq = run_pipeline(run_dir)
    except Exception as exc:   # noqa: BLE001 — top-level harness boundary; report and fail
        print("FATAL: pipeline did not complete: %s" % exc, file=sys.stderr)
        return 1

    fp = fingerprint(seq)
    print("\ngenome    : %s" % (run_dir / (PROJECT_NAME + "_genome.fasta")))
    print("fingerprint: %s" % format_fingerprint(fp))

    problems = check_plausible(seq)
    if problems:
        print("\nIMPLAUSIBLE genome:", file=sys.stderr)
        for p in problems:
            print("  - %s" % p, file=sys.stderr)
        return 1
    print("plausible : yes (within smoke bounds)")

    if args.golden:
        ok, msg = compare_to_golden(seq, args.golden)
        print("\n%s" % msg)
        return 0 if ok else 1

    print("\nNo golden supplied. If this genome is correct, bless it as the regression baseline:")
    print("  echo '%s' > tests/expected/smoke_assembly.fingerprint" % format_fingerprint(fp))
    print("then re-run with --golden tests/expected/smoke_assembly.fingerprint to lock it in.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
