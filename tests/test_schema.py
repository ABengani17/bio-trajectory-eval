import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bio_trajectory_eval.schema import AutomationPackage, Platform, load_package


class SchemaTests(unittest.TestCase):
    def test_load_manifest(self):
        package = load_package(ROOT / "examples" / "inert_dye_run.json")
        self.assertIsInstance(package, AutomationPackage)
        self.assertEqual(package.platform, Platform.OPENTRONS)
        self.assertEqual(package.samples[0].id, "blue_water")

    def test_rejects_duplicate_samples(self):
        raw = load_package(ROOT / "examples" / "inert_dye_run.json").model_dump()
        raw["samples"].append(raw["samples"][0])
        with self.assertRaises(ValueError):
            AutomationPackage.model_validate(raw)


if __name__ == "__main__":
    unittest.main()
