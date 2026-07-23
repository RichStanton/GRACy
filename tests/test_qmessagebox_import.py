"""Regression tests for BUG-6 (issue #23).

The "no files selected" guards (and other input-validation warnings) construct a
`QMessageBox`. Read Filtering, Genotyping and DB Submission import it; Assembly,
Annotation and SNP Calling used it without importing it. Once BUG-1 (#2) made the
guards actually fire, those three raised `NameError: name 'QMessageBox' is not defined`
to the terminal instead of showing the warning dialog.

Any module that *references* `QMessageBox` must also *import* it.

- ImportPresenceSourceTest — AST check across all six live Qt modules: if the source
  loads the `QMessageBox` name, an `import` of it must exist. No deps; protects every
  module against reintroduction.
- ImportBehaviourTest — each module, once loaded, exposes `QMessageBox` as a module
  global (so guard bodies can construct it). Requires the bundled interpreter
  (imports PyQt5); skipped otherwise. Run:
      src/conda/bin/python -m unittest discover -s tests
"""
import ast
import importlib.util
import os
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The six live PyQt5 modules whose guards construct a QMessageBox.
MODULES = {
    "readsFilteringQt": "src/scripts/readsFiltering/readsFilteringQt.py",
    "genotypingQt": "src/scripts/genotyping/genotypingQt.py",
    "dbsubmissionQt": "src/scripts/dbsubmission/dbsubmissionQt.py",
    "annotationQt": "src/scripts/annotation/annotationQt.py",
    "assemblyQt": "src/scripts/assembly/assemblyQt.py",
    "snpCallingQt": "src/scripts/snpCalling/snpCallingQt.py",
}


def _imports_qmessagebox(tree):
    """True if the module imports the QMessageBox name (directly or via alias)."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "QMessageBox" or alias.asname == "QMessageBox":
                    return True
        elif isinstance(node, ast.Import):
            for alias in node.names:
                # e.g. `import PyQt5.QtWidgets as QMessageBox` (unlikely, but complete)
                if alias.asname == "QMessageBox":
                    return True
    return False


def _references_qmessagebox(tree):
    """True if the module loads a bare `QMessageBox` name anywhere (guard bodies)."""
    return any(
        isinstance(node, ast.Name)
        and node.id == "QMessageBox"
        and isinstance(node.ctx, ast.Load)
        for node in ast.walk(tree)
    )


class ImportPresenceSourceTest(unittest.TestCase):
    def test_every_module_that_uses_qmessagebox_imports_it(self):
        for name, rel in MODULES.items():
            with open(os.path.join(REPO, rel)) as fh:
                tree = ast.parse(fh.read())
            if _references_qmessagebox(tree):
                self.assertTrue(
                    _imports_qmessagebox(tree),
                    f"{rel}: references QMessageBox but never imports it "
                    f"(guards will raise NameError when they fire — BUG-6)",
                )


def _load(name, rel):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, rel))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


try:
    _LOADED = {name: _load(name, rel) for name, rel in MODULES.items()}
    _IMPORT_ERR = None
except Exception as exc:  # heavy deps (PyQt5/matplotlib/Bio) absent outside conda
    _LOADED = None
    _IMPORT_ERR = exc


@unittest.skipUnless(_LOADED is not None, f"modules not importable: {_IMPORT_ERR}")
class ImportBehaviourTest(unittest.TestCase):
    def test_qmessagebox_resolvable_as_module_global(self):
        from PyQt5.QtWidgets import QMessageBox as RealQMessageBox

        for name, module in _LOADED.items():
            self.assertTrue(
                hasattr(module, "QMessageBox"),
                f"{name}: QMessageBox not importable at module scope (BUG-6)",
            )
            self.assertIs(getattr(module, "QMessageBox"), RealQMessageBox)


if __name__ == "__main__":
    unittest.main()
