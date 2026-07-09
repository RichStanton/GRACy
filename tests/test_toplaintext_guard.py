"""Regression tests for BUG-1 (issue #2).

The "no files selected" guard must call `toPlainText()`. Comparing the bare bound
method object (`...toPlainText`) to "" is always False, so the guard never fires and
the pipeline crashes instead of warning.

Two levels of coverage:
- GuardSourceTest — source-level regression across all six live Qt modules. Protects
  against the bug reappearing in any of them. No PyQt5 required.
- GuardBehaviourTest — proves the corrected idiom against a real QTextEdit widget.
  Skipped if PyQt5 is unavailable; run with the bundled interpreter:
      src/conda/bin/python -m unittest discover -s tests
"""
import os
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The six live PyQt5 modules whose "no files selected" guard was fixed.
GUARD_FILES = [
    "src/scripts/readsFiltering/readsFilteringQt.py",
    "src/scripts/snpCalling/snpCallingQt.py",
    "src/scripts/dbsubmission/dbsubmissionQt.py",
    "src/scripts/annotation/annotationQt.py",
    "src/scripts/assembly/assemblyQt.py",
    "src/scripts/genotyping/genotypingQt.py",
]


class GuardSourceTest(unittest.TestCase):
    def test_guards_call_the_method(self):
        for rel in GUARD_FILES:
            with open(os.path.join(REPO, rel)) as fh:
                src = fh.read()
            self.assertIn(
                "selectedFilesArea.toPlainText()", src,
                f"{rel}: guard should call toPlainText()",
            )
            # The buggy bare-method comparison must be gone.
            self.assertNotRegex(
                src, r"selectedFilesArea\.toPlainText\)",
                f"{rel}: bare toPlainText (missing parentheses) still present",
            )


try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtWidgets import QApplication, QTextEdit
    _HAVE_QT = True
except Exception:
    _HAVE_QT = False


@unittest.skipUnless(_HAVE_QT, "PyQt5 not available (run with src/conda/bin/python)")
class GuardBehaviourTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_empty_fires_populated_passes(self):
        w = QTextEdit()
        # Empty selection -> the corrected guard fires (True).
        self.assertTrue(str(w.toPlainText()) == "")
        # The bug it replaces: the bare method object is never "" -> never fires.
        self.assertFalse(str(w.toPlainText) == "")
        # Files present -> the corrected guard passes (False), pipeline proceeds.
        w.setPlainText("/data/sampleA_1.fastq")
        self.assertFalse(str(w.toPlainText()) == "")


if __name__ == "__main__":
    unittest.main()
