"""Fast guard for the issue-#11 end-to-end smoke harness.

The heavy work — actually running bowtie2/SPAdes/samtools on testDataset — lives in
tests/harness/smoke_assembly.py and is run manually (it needs the toolchain and minutes).
This unittest is the cheap counterpart: it imports the harness's *pure* checks and proves
they accept a plausible genome and reject the ways a run can go wrong (empty, truncated,
garbage bases, all-N, golden mismatch). If someone weakens those checks, this goes red in
under a second — no toolchain required.

Issue: #11 — End-to-end smoke test on testDataset/ + CI (safety net).
"""
import importlib.util
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HARNESS = REPO / "tests" / "harness" / "smoke_assembly.py"


def _load_harness():
    # Import by path — the pure checks have no PyQt import at module top, so this works on a
    # plain python3 without the toolchain. (PyQt is imported lazily inside run_pipeline.)
    spec = importlib.util.spec_from_file_location("smoke_assembly", str(HARNESS))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class SmokeHarnessWiring(unittest.TestCase):
    def test_harness_files_exist(self):
        self.assertTrue(HARNESS.is_file(), "smoke_assembly.py missing")
        self.assertTrue((REPO / "tests" / "harness" / "smoke_assembly.sh").is_file(),
                        "smoke_assembly.sh wrapper missing")
        self.assertTrue((REPO / "tests" / "fixtures" / "smoke_assembly.conf.template").is_file(),
                        "conf template missing")

    def test_conf_template_points_at_testdataset_reads(self):
        tmpl = (REPO / "tests" / "fixtures" / "smoke_assembly.conf.template").read_text()
        self.assertIn("@READS@/merlin_1.fastq", tmpl)
        self.assertIn("Project_name\tmerlin", tmpl,
                      "Project_name must stay 'merlin' — the harness derives the output path from it")


class PlausibilityChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h = _load_harness()

    def test_plausible_genome_passes(self):
        good = "ACGT" * (self.h.MIN_PLAUSIBLE_LEN // 4 + 100)
        self.assertEqual(self.h.check_plausible(good), [])

    def test_empty_is_rejected(self):
        self.assertEqual(self.h.check_plausible(""), ["genome is empty"])

    def test_truncated_is_rejected(self):
        problems = self.h.check_plausible("ACGT" * 100)   # ~400 bp, far below the floor
        self.assertTrue(any("too short" in p for p in problems), problems)

    def test_non_dna_is_rejected(self):
        garbage = ("ACGTX" * (self.h.MIN_PLAUSIBLE_LEN // 5 + 100))
        problems = self.h.check_plausible(garbage)
        self.assertTrue(any("non-DNA" in p for p in problems), problems)

    def test_all_n_is_rejected(self):
        alln = "N" * (self.h.MIN_PLAUSIBLE_LEN + 100)
        problems = self.h.check_plausible(alln)
        self.assertTrue(any("too many Ns" in p for p in problems), problems)

    def test_fingerprint_is_case_insensitive(self):
        self.assertEqual(self.h.fingerprint("ACGTACGT")["sha256"],
                         self.h.fingerprint("acgtacgt")["sha256"])

    def test_read_fasta_concatenates_records(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".fasta", delete=False) as fh:
            fh.write(">rec1\nACGT\nACGT\n>rec2\nTTTT\n")
            path = fh.name
        self.assertEqual(self.h.read_fasta_seq(path), "ACGTACGTTTTT")

    def test_golden_comparison_matches_and_differs(self):
        import tempfile
        seq = "ACGT" * 1000
        fp = self.h.fingerprint(seq)
        with tempfile.NamedTemporaryFile("w", suffix=".fp", delete=False) as fh:
            fh.write(self.h.format_fingerprint(fp))
            golden = fh.name
        ok, _ = self.h.compare_to_golden(seq, golden)
        self.assertTrue(ok, "identical sequence must match its own golden")
        bad, _ = self.h.compare_to_golden("TTTT" * 1000, golden)
        self.assertFalse(bad, "a different sequence must not match the golden")


if __name__ == "__main__":
    unittest.main()
