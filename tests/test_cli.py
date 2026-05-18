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

from bio_trajectory_eval.cli import cmd_report, cmd_validate


class CliTests(unittest.TestCase):
    def test_validate_prints_counts(self):
        output = StringIO()
        with redirect_stdout(output):
            cmd_validate(Namespace(data=str(ROOT / "data" / "tasks.jsonl")))
        text = output.getvalue()
        self.assertIn("validated", text)
        self.assertIn("protocol_intake", text)

    def test_report_prints_protocol_signal_summary(self):
        rows = [
            {"task_id": "task_0001", "task_type": "protocol_intake", "score": 100, "schema_valid": True},
            {"task_id": "task_0003", "task_type": "protocol_review", "score": 50, "schema_valid": False, "findings": ["missed seeded issue"]},
        ]
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".jsonl") as handle:
            for row in rows:
                handle.write(json.dumps(row) + "\n")
            handle.flush()
            output = StringIO()
            with redirect_stdout(output):
                cmd_report(Namespace(input=handle.name, fail_below=70, limit=10))
        text = output.getvalue()
        self.assertIn("protocol signal report", text)
        self.assertIn("protocol_review", text)
        self.assertIn("tasks below 70", text)


if __name__ == "__main__":
    unittest.main()
