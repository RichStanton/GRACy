"""Regression test: install.sh must provide libgomp so khmer can load (issue #11).

Background: khmer=3.0.0 (bioconda) ships a C extension (_khmer) that links against the
OpenMP runtime libgomp.so.1, but the package does not pull that runtime into this py37 env.
On a fresh install every khmer tool then dies at import:

    ImportError: libgomp.so.1: cannot open shared object file: No such file or directory

That breaks the assembly pipeline invisibly: interleave-reads.py / normalize-by-median.py
produce nothing, the de novo read set empties to 0 reads, and getBestAssembly.py aborts with
"range() arg 3 must not be zero" — the failure the #11 smoke test first surfaced.

The fix installs libgomp explicitly (conda-forge) before khmer, keeping the toolchain
self-contained rather than relying on a system gcc/libgomp being present. Two guards:

  * text guard (always runs): install.sh installs libgomp, and before khmer.
  * runtime guard (skips without the toolchain): `import khmer` actually succeeds.
"""
import os
import subprocess
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTALL_SH = os.path.join(REPO, "install.sh")
CONDA_PY = os.path.join(REPO, "src", "conda", "bin", "python")


class InstallLibgompGuard(unittest.TestCase):
    def setUp(self):
        with open(INSTALL_SH) as fh:
            self.text = fh.read()

    def test_install_sh_installs_libgomp(self):
        self.assertIn(
            "conda install -c conda-forge -y libgomp",
            self.text,
            "install.sh must install libgomp — khmer's _khmer extension needs libgomp.so.1 "
            "at import, and the bioconda khmer package does not pull it into the py37 env.",
        )

    def test_libgomp_installed_before_khmer(self):
        libgomp_at = self.text.find("libgomp")
        khmer_at = self.text.find("khmer=3.0.0")
        self.assertNotEqual(libgomp_at, -1, "no libgomp install found in install.sh")
        self.assertNotEqual(khmer_at, -1, "no khmer install found in install.sh")
        self.assertLess(
            libgomp_at, khmer_at,
            "libgomp must be installed before khmer so the khmer install/import can resolve "
            "its OpenMP runtime.",
        )


class KhmerImportsGuard(unittest.TestCase):
    """The real thing: on a machine with the toolchain, khmer must import."""

    @unittest.skipUnless(os.path.exists(CONDA_PY), "bundled toolchain (src/conda) not installed")
    def test_khmer_imports_in_bundled_env(self):
        result = subprocess.run(
            [CONDA_PY, "-c", "import khmer; print(khmer.__version__)"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        self.assertEqual(
            result.returncode, 0,
            "khmer failed to import in src/conda — libgomp.so.1 likely missing:\n%s"
            % result.stdout.decode(errors="replace"),
        )


if __name__ == "__main__":
    unittest.main()
