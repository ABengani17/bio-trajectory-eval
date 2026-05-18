import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bio_trajectory_eval.labbench_gate import BiosecurityGate
from bio_trajectory_eval.schema import Decision


class LabbenchGateTests(unittest.TestCase):
    def test_gate_passes_and_writes_audit_log(self):
        with tempfile.NamedTemporaryFile("r", encoding="utf-8", suffix=".jsonl") as handle:
            gate = BiosecurityGate(audit_log=handle.name)
            result = gate.assert_clearance(ROOT / "examples" / "pass_inert_opentrons.json")
            self.assertEqual(result.summary.decision, Decision.PASS)
            handle.seek(0)
            self.assertIn("pkg_inert_001", handle.read())

    def test_gate_fails_closed_on_block(self):
        gate = BiosecurityGate()
        with self.assertRaises(RuntimeError):
            gate.assert_clearance(ROOT / "examples" / "block_construct_missing_screening.json")


if __name__ == "__main__":
    unittest.main()
