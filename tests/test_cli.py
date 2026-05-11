import json
import sys
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bio_trajectory_eval.cli import cmd_report


class CliTests(unittest.TestCase):
    def test_report_prints_outcomes_and_diagnosis(self):
        rows = [
            {
                "difficulty": "tier_2",
                "trajectory_label": "compliant_throughout",
                "failure_mode": "under_sensitive",
            },
            {
                "difficulty": "tier_2",
                "trajectory_label": "redirected",
                "failure_mode": "as_expected",
            },
        ]
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".jsonl") as handle:
            for row in rows:
                handle.write(json.dumps(row) + "\n")
            handle.flush()
            output = StringIO()
            with redirect_stdout(output):
                cmd_report(Namespace(input=handle.name))

        text = output.getvalue()
        self.assertIn("outcomes", text)
        self.assertIn("diagnosis", text)
        self.assertIn("under_sensitive", text)
        self.assertIn("as_expected", text)


if __name__ == "__main__":
    unittest.main()
