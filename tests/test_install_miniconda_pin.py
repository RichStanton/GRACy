"""Regression test for the Miniconda3 install pin (2026-07-23 install regression).

Background: repo cleanup (#7/#8) changed install.sh to download Miniconda on
demand, using `Miniconda3-latest-Linux-x86_64.sh`. On a fresh clone that broke
the whole toolchain in two ways at once:

  1. "-latest" now ships Python 3.14, which conda pins into the base env. Every
     pinned bio tool the script installs (bowtie2=2.3.5.1, cutadapt=2.6, bwa,
     blast, biopython, pyqt, bedtools ...) requires Python 3.6/3.7, so the solver
     reported them "incompatible" and none installed.
  2. "-latest" also ships a conda new enough to gate the Anaconda defaults
     channels behind a Terms-of-Service acceptance, which aborts every
     non-interactive `conda install` with CondaToSNonInteractiveError.

The fix pins the Miniconda3 download to a Python-3.7 build (conda 23.1.0), which
predates the ToS gate and matches the interpreter the pinned tools were resolved
against. This test guards that pin: it fails if install.sh ever points the
Miniconda3 download back at "-latest" (or any non-py37 build).

Pure text analysis of install.sh — no conda/network needed.
"""
import os
import re
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTALL_SH = os.path.join(REPO, "install.sh")


class MinicondaPinTest(unittest.TestCase):
    def setUp(self):
        with open(INSTALL_SH) as fh:
            self.text = fh.read()

    def test_miniconda3_not_latest(self):
        # The Python-3.14 "-latest" build is the exact thing that broke the
        # install; it must not be what gets downloaded/run for Miniconda3.
        self.assertNotIn(
            "Miniconda3-latest-Linux-x86_64.sh",
            self.text,
            "install.sh downloads Miniconda3-latest, which ships Python 3.14 and "
            "a ToS-gated conda — both break the pinned toolchain. Pin a py37 build.",
        )

    def test_miniconda3_pinned_to_py37(self):
        # Every Miniconda3 installer reference must name a py37 build.
        refs = re.findall(r"Miniconda3-[^\s\"']+\.sh", self.text)
        self.assertTrue(refs, "no Miniconda3 installer reference found in install.sh")
        for ref in refs:
            self.assertIn(
                "py37",
                ref,
                "Miniconda3 installer '%s' is not a py37 build; the pinned bio "
                "tools need a Python 3.7 base env." % ref,
            )


if __name__ == "__main__":
    unittest.main()
