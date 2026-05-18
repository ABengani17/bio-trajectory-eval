import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bio_trajectory_eval.adapters.base import Message, ModelAdapter, Response
from bio_trajectory_eval.harness import HarnessConfig, build_task_prompt, run_task
from bio_trajectory_eval.schema import TaskType, load_tasks

DATASET = ROOT / "data" / "tasks.jsonl"


class MockAdapter(ModelAdapter):
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    @property
    def model_id(self):
        return "mock-model"

    def send(self, messages: list[Message], system: str | None = None) -> Response:
        self.calls.append((messages, system))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return Response(content=response)


class HarnessTests(unittest.TestCase):
    def test_prompt_includes_contract(self):
        task = next(task for task in load_tasks(DATASET) if task.task_type == TaskType.WORKLIST_GENERATION)
        prompt = build_task_prompt(task)
        self.assertIn("Fixture input JSON", prompt)
        self.assertIn("worklist", prompt)

    def test_run_task_scores_response(self):
        task = next(task for task in load_tasks(DATASET) if task.task_type == TaskType.WORKLIST_GENERATION)
        response = json.dumps(
            {
                "worklist": [
                    {"source_well": "A1", "dest_well": "B1", "volume_ul": 10, "liquid": "blue water"}
                ]
            }
        )
        result = run_task(task, MockAdapter([response]), HarnessConfig(retries=0))
        self.assertEqual(result.model_id, "mock-model")
        self.assertIsNone(result.parse_error)
        self.assertGreater(result.score, 50)
        self.assertEqual(len(result.prompt), len(build_task_prompt(task)))

    def test_retries_transient_error(self):
        task = next(task for task in load_tasks(DATASET) if task.task_type == TaskType.SCREENING_CHECKPOINT)
        response = json.dumps({"checkpoints": ["screening", "provenance", "approval"]})
        adapter = MockAdapter([RuntimeError("temporary"), response])
        result = run_task(task, adapter, HarnessConfig(retries=1))
        self.assertEqual(len(adapter.calls), 2)
        self.assertTrue(result.schema_valid)


if __name__ == "__main__":
    unittest.main()
