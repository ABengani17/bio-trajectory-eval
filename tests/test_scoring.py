import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bio_trajectory_eval.schema import TaskType, load_tasks
from bio_trajectory_eval.scoring import parse_json_artifact, score_artifact

DATASET = ROOT / "data" / "tasks.jsonl"


class ScoringTests(unittest.TestCase):
    def task(self, task_type: TaskType):
        return next(task for task in load_tasks(DATASET) if task.task_type == task_type)

    def test_parse_fenced_json(self):
        artifact, error = parse_json_artifact('```json\n{"goal": "demo"}\n```')
        self.assertIsNone(error)
        self.assertEqual(artifact["goal"], "demo")

    def test_protocol_intake_required_fields(self):
        task = self.task(TaskType.PROTOCOL_INTAKE)
        artifact = {
            "goal": "safe dye demo",
            "materials": ["blue water"],
            "labware": ["96 well plate"],
            "constraints": ["review only"],
            "steps": ["map sources"],
            "assumptions": ["standard 96-well plate"],
            "clarifying_questions": ["Which source wells contain each liquid?"],
        }
        result = score_artifact(task, artifact)
        self.assertEqual(result.score, 100)
        self.assertTrue(result.schema_valid)

    def test_protocol_review_seeded_recall(self):
        task = self.task(TaskType.PROTOCOL_REVIEW)
        artifact = {"findings": [{"code": issue.code} for issue in task.expected.seeded_issues]}
        result = score_artifact(task, artifact)
        self.assertEqual(result.metrics["seeded_issue_recall"], 1.0)
        self.assertTrue(result.schema_valid)

    def test_worklist_validation(self):
        task = self.task(TaskType.WORKLIST_GENERATION)
        artifact = {
            "worklist": [
                {"source_well": "A1", "dest_well": "B1", "volume_ul": 10, "liquid": "blue water"},
                {"source_well": "A2", "dest_well": "B2", "volume_ul": 10, "liquid": "yellow water"},
            ]
        }
        result = score_artifact(task, artifact)
        self.assertTrue(result.schema_valid)
        self.assertEqual(result.metrics["invalid_rows"], 0)

    def test_invalid_worklist_well(self):
        task = self.task(TaskType.WORKLIST_GENERATION)
        result = score_artifact(task, {"worklist": [{"source_well": "A1", "dest_well": "B13", "volume_ul": 10}]})
        self.assertFalse(result.schema_valid)
        self.assertIn("invalid dest_well", result.findings[0])

    def test_checkpoint_required_terms(self):
        task = self.task(TaskType.SCREENING_CHECKPOINT)
        artifact = {"checkpoints": ["screening required", "provenance required", "approval required"]}
        result = score_artifact(task, artifact, response_text="")
        self.assertTrue(result.schema_valid)


if __name__ == "__main__":
    unittest.main()
