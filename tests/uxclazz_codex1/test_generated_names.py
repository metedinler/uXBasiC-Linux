"""User-visible generator contract regressions; independent of compiler binaries."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "tools/uxclazz/uxclazz.py"
spec = importlib.util.spec_from_file_location("uxclazz_codex1_test_module", GENERATOR)
uxclazz = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = uxclazz
spec.loader.exec_module(uxclazz)


class GeneratedNameTests(unittest.TestCase):
    def rejects(self, source, message):
        with self.assertRaisesRegex(uxclazz.UXClazzError, message):
            uxclazz.parse_text(source, "test.uxclz")

    def test_case_insensitive_field_duplicate(self):
        self.rejects("CLAZZ DATA Box\nx AS I32\nX AS I32\nEND CLAZZ", r"test.uxclz:3: duplicate field.*test.uxclz:2")

    def test_trait_accessor_collides_with_field_accessor(self):
        self.rejects("CLAZZ DATA Box\nUSES Logger\nLoggerPart AS I32\nEND CLAZZ", r"test.uxclz:2: generated member collision.*test.uxclz:3")

    def test_readonly_still_conflicts_with_trait_getter(self):
        self.rejects("CLAZZ DATA Box\nUSES Logger\nREADONLY LoggerPart AS I32\nEND CLAZZ", "GetLoggerPart")

    def test_duplicate_traits(self):
        self.rejects("CLAZZ DATA Box\nUSES Logger, logger\nEND CLAZZ", "generated member collision")

    def test_duplicate_classes(self):
        self.rejects("CLAZZ DATA Box\nEND CLAZZ\nCLAZZ DATA box\nEND CLAZZ", "duplicate class box")

    def test_unknown_derive_is_not_silently_ignored(self):
        self.rejects("CLAZZ DATA Box\nDERIVE HASHH\nEND CLAZZ", "unsupported DERIVE HASHH")

    def test_valid_composition_and_readonly_contract(self):
        source = "CLAZZ ENTITY Box\nUSES Logger\nREADONLY Name AS STRING\nDERIVE EQ, EQUALS, HASH, CLONE, TOSTRING, JSON\nEND CLAZZ"
        classes = uxclazz.parse_text(source)
        output = uxclazz.render(classes, "valid.uxclz")
        self.assertEqual(output.count("METHOD Equals("), 1)
        self.assertEqual(output.count("METHOD GetLoggerPart("), 1)
        self.assertIn("METHOD GetName(", output)
        self.assertNotIn("METHOD SetName(", output)
        self.assertIn("MAGIC HASH", output)
        self.assertEqual([f.name for f in classes[0].fields[:2]], ["Id", "Version"])

    def test_repository_sample_remains_valid(self):
        sample = ROOT / "examples/uxclazz/fish_sample.uxclz"
        classes = uxclazz.parse_text(sample.read_text(encoding="utf-8"), str(sample))
        self.assertEqual(len(classes), 2)
        output = uxclazz.render(classes, sample.name)
        self.assertIn("CLASS FishSample", output)
        self.assertIn("CLASS Customer", output)


if __name__ == "__main__":
    unittest.main()
