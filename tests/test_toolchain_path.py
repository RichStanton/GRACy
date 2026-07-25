"""Regression tests for #33 — GRACy must put its own conda bins on PATH.

Why this exists
---------------
GRACy invokes its tools by absolute path (`<install>/src/conda/bin/<tool>`), so PATH is not
needed to *find* them. But some bundled wrappers shell out to bare command names internally.
`src/conda/bin/varscan` runs plain `java`; on a machine with no system java that wrapper exits
**127**, and because every call site uses `os.system(...)` — which discards the exit code — the
pipeline carries on and applies an empty VCF. Silent wrong output, in the assembly module's
consensus steps (assemblyQt.py 532/599/666/1005) as well as SNP calling.

The fix is for the application to prepend its own `src/conda/bin` and `src/conda2/bin` to PATH
before shelling out to anything. These tests fail if that stops happening.

The runtime guard below is the one that matters: it runs the real varscan wrapper.
"""

import os
import subprocess
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src", "scripts", "utils"))

MODULES = [
    "readsFiltering/readsFilteringQt.py",
    "assembly/assemblyQt.py",
    "genotyping/genotypingQt.py",
    "annotation/annotationQt.py",
    "snpCalling/snpCallingQt.py",
    "dbsubmission/dbsubmissionQt.py",
]


class TestEnsureToolPath(unittest.TestCase):
    """Behaviour of the helper itself."""

    def setUp(self):
        import toolpath

        self.toolpath = toolpath
        self._saved = os.environ.get("PATH", "")

    def tearDown(self):
        os.environ["PATH"] = self._saved

    def test_prepends_both_conda_bins(self):
        os.environ["PATH"] = "/usr/bin"
        self.toolpath.ensure_tool_path(REPO + "/")
        parts = os.environ["PATH"].split(os.pathsep)
        self.assertEqual(parts[0], os.path.join(REPO, "src", "conda", "bin"))
        self.assertEqual(parts[1], os.path.join(REPO, "src", "conda2", "bin"))

    def test_preserves_existing_path(self):
        os.environ["PATH"] = "/usr/bin:/bin"
        self.toolpath.ensure_tool_path(REPO + "/")
        self.assertTrue(os.environ["PATH"].endswith("/usr/bin:/bin"))

    def test_is_idempotent(self):
        os.environ["PATH"] = "/usr/bin"
        self.toolpath.ensure_tool_path(REPO + "/")
        once = os.environ["PATH"]
        self.toolpath.ensure_tool_path(REPO + "/")
        self.assertEqual(once, os.environ["PATH"], "repeated calls must not stack duplicates")

    def test_tolerates_missing_path_var(self):
        os.environ.pop("PATH", None)
        self.toolpath.ensure_tool_path(REPO + "/")
        self.assertIn(os.path.join(REPO, "src", "conda", "bin"), os.environ["PATH"])

    def test_accepts_directory_without_trailing_slash(self):
        os.environ["PATH"] = "/usr/bin"
        self.toolpath.ensure_tool_path(REPO)
        self.assertIn(os.path.join(REPO, "src", "conda", "bin"), os.environ["PATH"])


class TestModulesWireItUp(unittest.TestCase):
    """Every GUI module must call the helper — a new module must not silently miss it."""

    def test_every_module_calls_ensure_tool_path_in_setupui(self):
        missing = []
        for rel in MODULES:
            with open(os.path.join(REPO, "src", "scripts", rel)) as handle:
                source = handle.read()
            if "ensure_tool_path(installationDirectory)" not in source:
                missing.append(rel)
        self.assertEqual([], missing, "these modules never put the toolchain on PATH: %s" % missing)

    def test_launcher_calls_ensure_tool_path(self):
        with open(os.path.join(REPO, "src", ".GRACy_main.py")) as handle:
            source = handle.read()
        self.assertIn("ensure_tool_path", source, "the Tkinter launcher must set PATH for its children")


class TestVarscanActuallyRuns(unittest.TestCase):
    """The runtime guard: the real wrapper, the real failure from #33.

    Skipped when the toolchain isn't installed. When it is, this is the test that would have
    caught #33 — varscan exits 127 without java on PATH.
    """

    def setUp(self):
        self.varscan = os.path.join(REPO, "src", "conda", "bin", "varscan")
        if not os.path.exists(self.varscan):
            self.skipTest("toolchain not installed (no src/conda/bin/varscan)")

    def test_varscan_runs_with_helper_applied(self):
        import toolpath

        env = dict(os.environ)
        env["PATH"] = "/usr/bin:/bin"  # a PATH with no java, as on the dev box
        env = toolpath.tool_path_env(REPO + "/", env)

        proc = subprocess.run(
            [self.varscan],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        output = proc.stdout.decode("utf-8", "replace")
        self.assertNotIn("java: command not found", output)
        self.assertNotEqual(127, proc.returncode, "varscan still can't find java — #33 is back")
        self.assertIn("VarScan", output, "expected varscan's own usage banner, got: %s" % output[:400])


if __name__ == "__main__":
    unittest.main()
