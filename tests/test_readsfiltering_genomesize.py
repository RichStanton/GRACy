"""Regression tests for BUG-5 (issue #6).

`readsFilteringQt.py` divided the aligned breadth by the HCMV genome size to get a
coverage fraction, with the magic number `235646.0` hardcoded at two sites. Extracted
to a single named constant, `HCMV_GENOME_SIZE`, referenced in both coverage calculations.

- GenomeSizeConstantTest — the constant exists and keeps the exact value, so coverage
  numbers are unchanged for the HCMV reference. Requires the bundled interpreter
  (imports PyQt5/matplotlib); skipped otherwise.
- SourceGuardTest — the literal appears once (the definition) and both divisions use the
  constant. No deps.
"""
import importlib.util
import os
import re
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(REPO, "src/scripts/readsFiltering/readsFilteringQt.py")


def _load_module():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    spec = importlib.util.spec_from_file_location("readsFilteringQt", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


try:
    readsFilteringQt = _load_module()
    _IMPORT_ERR = None
except Exception as exc:  # heavy deps (PyQt5/matplotlib) absent outside conda
    readsFilteringQt = None
    _IMPORT_ERR = exc


@unittest.skipUnless(readsFilteringQt is not None, f"readsFilteringQt not importable: {_IMPORT_ERR}")
class GenomeSizeConstantTest(unittest.TestCase):
    def test_constant_keeps_the_hcmv_reference_length(self):
        # Value unchanged => coverage fractions are identical to the old literal.
        self.assertEqual(readsFilteringQt.HCMV_GENOME_SIZE, 235646.0)


class SourceGuardTest(unittest.TestCase):
    """No PyQt5 needed: the magic number must be defined once and shared."""

    def setUp(self):
        with open(MODULE_PATH) as fh:
            self.src = fh.read()

    def test_literal_defined_exactly_once(self):
        self.assertEqual(
            self.src.count("235646.0"), 1,
            "the genome size literal should appear only in the constant definition",
        )

    def test_both_coverage_sites_use_the_constant(self):
        self.assertIn("HCMV_GENOME_SIZE = 235646.0", self.src)
        self.assertEqual(
            len(re.findall(r"breadthValue\s*/\s*HCMV_GENOME_SIZE", self.src)), 2,
            "both coverage calculations should divide by HCMV_GENOME_SIZE",
        )


if __name__ == "__main__":
    unittest.main()
