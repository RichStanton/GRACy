"""Regression tests for BUG-2 (issue #3).

`completeGenome.py` computes `lastPortion = genomeSeq[-20000:]` but the following write
emitted `firstPortion` into the `>lastPortion` record — silently replacing the 3' end
with a copy of the 5' end (in fact the 5' end of an *earlier* genome, since `genomeSeq`
is reassigned from `newGenome1.fasta` beforehand). The record must carry `lastPortion`.

The script is a top-to-bottom pipeline step (reads files, needs Bio/blast/ragout output),
so it is not importable in isolation. Both checks are therefore stdlib-only AST analysis:

- LastPortionRecordTest — the `>lastPortion` record is written with the `lastPortion`
  variable, and `firstPortion` no longer appears in that write.
- FabricatedSequenceTest — on a fabricated genome the two portions genuinely differ, so
  writing `firstPortion` under `>lastPortion` would corrupt the sequence; proves the fix
  changes the emitted content, not just a label.
"""
import ast
import os
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(REPO, "src/scripts/assembly/utils/completeGenome.py")


def _str_value(node):
    """String literal value, compatible with 3.7 (ast.Str) and 3.8+ (ast.Constant)."""
    if isinstance(node, ast.Str):  # Python 3.7
        return node.s
    if isinstance(node, ast.Constant) and isinstance(node.value, str):  # 3.8+
        return node.value
    return None


def _lastportion_write_names():
    """Names concatenated into the outfile.write(">lastPortion\\n"+...+"\\n") call."""
    with open(MODULE_PATH) as fh:
        tree = ast.parse(fh.read())
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "write"
            and node.args
        ):
            arg = node.args[0]
            literals = [s for s in (_str_value(n) for n in ast.walk(arg)) if s is not None]
            if any(lit.startswith(">lastPortion") for lit in literals):
                return sorted(
                    n.id for n in ast.walk(arg) if isinstance(n, ast.Name)
                )
    return None


class LastPortionRecordTest(unittest.TestCase):
    def test_record_writes_lastportion_not_firstportion(self):
        names = _lastportion_write_names()
        self.assertIsNotNone(names, "could not find the >lastPortion write call")
        self.assertIn(
            "lastPortion", names,
            "the >lastPortion record must be written from lastPortion (BUG-2)",
        )
        self.assertNotIn(
            "firstPortion", names,
            "the >lastPortion record must not write firstPortion (BUG-2)",
        )


class FabricatedSequenceTest(unittest.TestCase):
    def test_first_and_last_portions_differ_so_the_fix_changes_content(self):
        # 5' run of A, spacer, 3' run of G — the two 20 kb ends are unmistakably distinct.
        genomeSeq = "A" * 20000 + "C" * 5000 + "G" * 20000
        firstPortion = genomeSeq[:20000]
        lastPortion = genomeSeq[-20000:]
        self.assertNotEqual(
            firstPortion, lastPortion,
            "fabricated ends must differ for the test to be meaningful",
        )
        self.assertEqual(lastPortion, "G" * 20000)
        # The corrected write emits lastPortion; assert that is what the source now uses.
        self.assertIn("lastPortion", _lastportion_write_names() or [])


if __name__ == "__main__":
    unittest.main()
