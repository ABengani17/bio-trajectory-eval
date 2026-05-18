import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bio_trajectory_eval.checks import scan_package
from bio_trajectory_eval.schema import Decision, load_package


class ChecksTests(unittest.TestCase):
    def scan(self, name: str):
        return scan_package(load_package(ROOT / "examples" / name))

    def test_inert_package_passes(self):
        result = self.scan("pass_inert_opentrons.json")
        self.assertEqual(result.summary.decision, Decision.PASS)
        self.assertEqual(result.summary.finding_count, 0)

    def test_environmental_samples_route_to_review(self):
        result = self.scan("review_environmental_samples.json")
        codes = {finding.code for finding in result.findings}
        self.assertEqual(result.summary.decision, Decision.REVIEW)
        self.assertIn("missing_provenance", codes)
        self.assertIn("missing_biosafety_review", codes)
        self.assertIn("missing_decontamination_plan", codes)

    def test_missing_construct_screening_blocks(self):
        result = self.scan("block_construct_missing_screening.json")
        codes = {finding.code for finding in result.findings}
        self.assertEqual(result.summary.decision, Decision.BLOCK)
        self.assertIn("missing_sequence_screening", codes)
        self.assertIn("missing_construct_approval", codes)
        self.assertIn("invalid_destination_well", codes)


if __name__ == "__main__":
    unittest.main()
