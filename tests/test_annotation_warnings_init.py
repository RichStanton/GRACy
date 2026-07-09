"""Regression tests for BUG-4 (issue #5).

`annotationQt.py` has no `import warnings`, so `warnings` is a function-local, assigned
partway through the annotation loop (`warnings = []`). On the paths that reach the early
"Check Exonerate output" loops first, `warnings.append(...)` runs *before* that
assignment, raising `UnboundLocalError: local variable 'warnings' referenced before
assignment`. The list must be initialised before its first reference on every path.

The check is a stdlib-only AST analysis (no PyQt5 / conda needed): the first assignment
to `warnings` must appear before the first read of it.
"""
import ast
import os
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(REPO, "src/scripts/annotation/annotationQt.py")


class WarningsInitialisedBeforeUseTest(unittest.TestCase):
    def setUp(self):
        with open(MODULE_PATH) as fh:
            self.tree = ast.parse(fh.read())

    def _warnings_lines(self, ctx):
        return sorted(
            node.lineno
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Name)
            and node.id == "warnings"
            and isinstance(node.ctx, ctx)
        )

    def test_first_assignment_precedes_first_use(self):
        stores = self._warnings_lines(ast.Store)  # `warnings = ...`
        loads = self._warnings_lines(ast.Load)     # `warnings.append(...)`
        self.assertTrue(stores, "warnings is never assigned")
        self.assertTrue(loads, "expected warnings to be used via .append")
        self.assertLess(
            stores[0], loads[0],
            f"warnings first assigned at line {stores[0]} but first used at line "
            f"{loads[0]} -> UnboundLocalError on that path",
        )


if __name__ == "__main__":
    unittest.main()
