import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bio_trajectory_eval.schema import ProtocolTask, TaskType, load_tasks

DATASET = ROOT / "data" / "tasks.jsonl"


class SchemaTests(unittest.TestCase):
    def test_dataset_loads(self):
        tasks = load_tasks(DATASET)
        self.assertGreaterEqual(len(tasks), 10)
        self.assertTrue(all(isinstance(task, ProtocolTask) for task in tasks))

    def test_all_task_types_present(self):
        observed = {task.task_type for task in load_tasks(DATASET)}
        self.assertEqual(observed, set(TaskType))

    def test_required_core_fields(self):
        for task in load_tasks(DATASET):
            dumped = task.model_dump()
            for field in ("id", "task_type", "title", "intent", "input", "expected", "notes"):
                self.assertIn(field, dumped)


if __name__ == "__main__":
    unittest.main()
