import sys
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bio_trajectory_eval.cli import cmd_report, cmd_scan, cmd_validate


class CliTests(unittest.TestCase):
    def test_validate_prints_manifest_summary(self):
        output = StringIO()
        with redirect_stdout(output):
            cmd_validate(Namespace(manifest=str(ROOT / "examples" / "pass_inert_opentrons.json")))
        text = output.getvalue()
        self.assertIn("validated pkg_inert_001", text)
        self.assertIn("platform: opentrons", text)

    def test_scan_and_report(self):
        with tempfile.NamedTemporaryFile("w+", encoding="utf-8", suffix=".json") as handle:
            cmd_scan(
                Namespace(
                    manifest=str(ROOT / "examples" / "block_construct_missing_screening.json"),
                    opentrons_protocol=None,
                    out=handle.name,
                )
            )
            output = StringIO()
            with redirect_stdout(output):
                cmd_report(Namespace(input=handle.name))
        text = output.getvalue()
        self.assertIn("decision: block", text)
        self.assertIn("missing_sequence_screening", text)


if __name__ == "__main__":
    unittest.main()
