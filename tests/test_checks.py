import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bio_trajectory_eval.checks import scan_package
from bio_trajectory_eval.schema import Decision, FindingAction, Policy, load_package


class ChecksTests(unittest.TestCase):
    def scan(self, name: str):
        return scan_package(load_package(ROOT / "examples" / name))

    def test_inert_package_passes(self):
        result = self.scan("inert_dye_run.json")
        self.assertEqual(result.summary.decision, Decision.PASS)
        self.assertEqual(result.summary.finding_count, 0)

    def test_environmental_samples_route_to_review(self):
        result = self.scan("environmental_sample_review.json")
        codes = {finding.code for finding in result.findings}
        self.assertEqual(result.summary.decision, Decision.REVIEW)
        self.assertIn("missing_provenance", codes)
        self.assertIn("missing_biosafety_review", codes)
        self.assertIn("missing_decontamination_plan", codes)

    def test_missing_construct_screening_blocks(self):
        result = self.scan("construct_screening_hold.json")
        codes = {finding.code for finding in result.findings}
        self.assertEqual(result.summary.decision, Decision.BLOCK)
        self.assertIn("missing_sequence_screening", codes)
        self.assertIn("missing_construct_approval", codes)
        self.assertIn("invalid_destination_well", codes)

    def test_policy_can_escalate_review_to_block(self):
        package = load_package(ROOT / "examples" / "environmental_sample_review.json")
        policy = Policy(finding_actions={"missing_biosafety_review": FindingAction.BLOCK_RUN})
        result = scan_package(package, policy)
        self.assertEqual(result.summary.decision, Decision.BLOCK)


if __name__ == "__main__":
    unittest.main()
