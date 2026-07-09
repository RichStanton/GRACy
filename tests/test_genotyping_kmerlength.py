"""Regression tests for BUG-3 (issue #4).

`genotypingQt.py` loads read k-mers in two blocks. The first (dedupFile1) enumerated
k-mers of length `kmerLength` (derived from the k-mer database); the second (dedupFile2)
hardcoded 17-mers (`range(0, len-16)` + `[a:a+17]`), so the two blocks agreed only when
`kmerLength == 17` and counts drifted silently for any other k-mer length.

Both blocks now share `collectKmers(sequence, kmerLength)`, so enumeration tracks
`kmerLength` everywhere.

- CollectKmersTest  — behaviour of the shared helper. Requires the bundled interpreter
  (imports PyQt5/matplotlib/Bio); skipped otherwise. Run:
      src/conda/bin/python -m unittest discover -s tests
- SourceGuardTest   — the hardcoded 17-mer literals are gone from the loader. No deps.
"""
import importlib.util
import os
import re
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(REPO, "src/scripts/genotyping/genotypingQt.py")


def _load_module():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    spec = importlib.util.spec_from_file_location("genotypingQt", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


try:
    genotypingQt = _load_module()
    _IMPORT_ERR = None
except Exception as exc:  # heavy deps (PyQt5/matplotlib/Bio) absent outside conda
    genotypingQt = None
    _IMPORT_ERR = exc


@unittest.skipUnless(genotypingQt is not None, f"genotypingQt not importable: {_IMPORT_ERR}")
class CollectKmersTest(unittest.TestCase):
    def test_enumerates_every_kmer_of_the_given_length(self):
        # "ABCDE" with k=3 -> ABC, BCD, CDE
        self.assertEqual(genotypingQt.collectKmers("ABCDE", 3), ["ABC", "BCD", "CDE"])

    def test_range_and_slice_track_kmerLength(self):
        seq = "ACGTACGTAC"  # length 10
        for k in (4, 6, 8, 17):
            kmers = genotypingQt.collectKmers(seq, k)
            expected = max(0, len(seq) - k + 1)
            self.assertEqual(len(kmers), expected, f"k={k}: wrong count")
            self.assertTrue(all(len(x) == k for x in kmers), f"k={k}: wrong slice length")

    def test_boundaries(self):
        self.assertEqual(genotypingQt.collectKmers("ACG", 5), [])        # shorter than k
        self.assertEqual(genotypingQt.collectKmers("ACGTA", 5), ["ACGTA"])  # len == k


class SourceGuardTest(unittest.TestCase):
    """No PyQt5 needed: the hardcoded 17-mer literals must be gone from the loader."""

    def test_no_hardcoded_kmer_literals(self):
        with open(MODULE_PATH) as fh:
            src = fh.read()
        self.assertNotIn("a:a+17", src, "hardcoded 17-mer slice still present")
        self.assertNotRegex(
            src, r"len\([A-Za-z_]+\)\s*-\s*16\)",
            "hardcoded `len(...)-16` k-mer range still present",
        )
        self.assertIn("collectKmers", src, "read loops should share collectKmers")


if __name__ == "__main__":
    unittest.main()
