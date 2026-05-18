import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bio_trajectory_eval.opentrons import read_opentrons_metadata


class OpentronsTests(unittest.TestCase):
    def test_reads_metadata_and_requirements(self):
        metadata = read_opentrons_metadata(ROOT / "examples" / "opentrons_demo_protocol.py")
        self.assertEqual(metadata.protocol_name, "Colored water plate demo")
        self.assertEqual(metadata.robot_type, "OT-2")
        self.assertEqual(metadata.api_level, "2.16")


if __name__ == "__main__":
    unittest.main()
