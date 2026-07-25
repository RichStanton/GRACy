"""Regression test: SPAdes runs from its own env, not the segfaulting pinned 3.12 (ADR-0002).

Background: the pinned `spades=3.12` (2018) segfaults on modern glibc (#30), which blocked the
#11 smoke test. The fix upgrades to SPAdes 4.x installed in a dedicated env (`src/condaSpades`)
so the py37 base env is left intact (ADR-0002). Guards:

  * text guards (always run): install.sh creates the condaSpades env with spades 4.x and does NOT
    install spades=3.12 into the base env; the two call sites invoke src/condaSpades.
  * runtime guard (skips without the env): src/condaSpades/bin/spades.py actually runs here.
"""
import os
import subprocess
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTALL_SH = os.path.join(REPO, "install.sh")
SPADES_PY = os.path.join(REPO, "src", "condaSpades", "bin", "spades.py")
CALL_SITES = [
    os.path.join(REPO, "src", "scripts", "assembly", "utils", "getBestAssembly.py"),
    os.path.join(REPO, "src", "scripts", "assembly", "utils", "createCenterScaffold.py"),
]


class InstallCreatesDedicatedEnv(unittest.TestCase):
    def setUp(self):
        with open(INSTALL_SH) as fh:
            self.text = fh.read()

    def test_creates_condaspades_env_with_spades4(self):
        self.assertIn("create -p ./src/condaSpades", self.text,
                      "install.sh must create the dedicated src/condaSpades env")
        self.assertIn("spades=4", self.text, "install.sh must install SPAdes 4.x")

    def test_does_not_install_spades312_in_base(self):
        # The segfaulting build must no longer be installed into the py37 base env.
        self.assertNotIn("conda install -c bioconda -y  spades=3.12", self.text,
                         "spades=3.12 must not be installed into the base env (it segfaults, #30)")


class CallSitesUseDedicatedEnv(unittest.TestCase):
    def test_call_sites_invoke_condaspades(self):
        for path in CALL_SITES:
            with open(path) as fh:
                text = fh.read()
            self.assertIn("src/condaSpades/bin/spades.py", text,
                          "%s must call SPAdes from src/condaSpades" % os.path.basename(path))
            self.assertNotIn("src/conda/bin/spades.py", text,
                             "%s still calls the base-env spades.py" % os.path.basename(path))


class SpadesActuallyRuns(unittest.TestCase):
    @unittest.skipUnless(os.path.exists(SPADES_PY), "src/condaSpades not installed")
    def test_spades_version_runs(self):
        py = os.path.join(REPO, "src", "condaSpades", "bin", "python")
        result = subprocess.run([py, SPADES_PY, "--version"],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = result.stdout.decode(errors="replace")
        self.assertEqual(result.returncode, 0, "spades.py --version failed:\n%s" % out)
        self.assertIn("v4", out, "expected SPAdes 4.x, got: %s" % out.strip())


if __name__ == "__main__":
    unittest.main()
