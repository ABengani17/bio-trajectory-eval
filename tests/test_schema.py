import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bio_trajectory_eval.schema import Difficulty, ProxyDomain, Trajectory, load_trajectories

DATASET = ROOT / "data" / "trajectories.jsonl"


class SchemaTests(unittest.TestCase):
    def test_dataset_loads(self):
        trajectories = load_trajectories(DATASET)
        self.assertGreaterEqual(len(trajectories), 25)
        self.assertLessEqual(len(trajectories), 40)
        self.assertTrue(all(isinstance(item, Trajectory) for item in trajectories))

    def test_required_fields_are_present(self):
        for trajectory in load_trajectories(DATASET):
            dumped = trajectory.model_dump()
            for field in (
                "id",
                "proxy_domain",
                "shape_of_real_workflow",
                "difficulty",
                "turns",
                "trajectory_level_concern",
                "expected_trajectory_outcome",
                "notes",
            ):
                self.assertIn(field, dumped)

    def test_enums_are_closed(self):
        for trajectory in load_trajectories(DATASET):
            self.assertIsInstance(trajectory.proxy_domain, ProxyDomain)
            self.assertIsInstance(trajectory.difficulty, Difficulty)

    def test_turn_indices_are_contiguous(self):
        for trajectory in load_trajectories(DATASET):
            self.assertEqual(
                [turn.turn_index for turn in trajectory.turns],
                list(range(len(trajectory.turns))),
            )


if __name__ == "__main__":
    unittest.main()
