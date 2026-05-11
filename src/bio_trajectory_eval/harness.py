from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from time import sleep

from bio_trajectory_eval.adapters.base import Message, ModelAdapter
from bio_trajectory_eval.assessment import assess_outcome
from bio_trajectory_eval.schema import Trajectory
from bio_trajectory_eval.scoring import TrajectoryLabel, TurnLabel, score_trajectory, score_turn_rules


@dataclass(frozen=True)
class HarnessConfig:
    max_turns: int = 8
    timeout_seconds: int = 60
    retries: int = 2
    early_stop_on_refusal: bool = True
    system_prompt: str | None = None


@dataclass(frozen=True)
class TurnResult:
    turn_index: int
    user_message: str
    expected_handling: str
    expected_rationale: str
    model_response: str
    handling_label: TurnLabel
    scoring_rationale: str


@dataclass(frozen=True)
class TrajectoryResult:
    trajectory_id: str
    proxy_domain: str
    difficulty: str
    shape_of_real_workflow: str
    trajectory_level_concern: str
    expected_trajectory_outcome: str
    model_id: str
    run_started_at: str
    config: dict
    turns: list[TurnResult]
    trajectory_label: TrajectoryLabel
    expectation_met: bool
    failure_mode: str
    first_restrictive_turn: int | None
    stopped_early: bool
    stopped_at_turn: int | None
    refusal_text: str | None

    def to_json_dict(self) -> dict:
        data = asdict(self)
        data["trajectory_label"] = self.trajectory_label.value
        for turn in data["turns"]:
            turn["handling_label"] = turn["handling_label"].value
        return data


def _send_with_retries(
    model: ModelAdapter,
    messages: list[Message],
    system: str | None,
    retries: int,
) -> str:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return model.send(messages=messages, system=system).content
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                sleep(min(2**attempt, 8))
    raise RuntimeError(f"model call failed after {retries + 1} attempts: {last_error}") from last_error


def run_trajectory(
    trajectory: Trajectory,
    model: ModelAdapter,
    config: HarnessConfig,
) -> TrajectoryResult:
    messages: list[Message] = []
    turn_results: list[TurnResult] = []
    stopped_early = False
    stopped_at_turn: int | None = None
    refusal_text: str | None = None

    for turn in trajectory.turns[: config.max_turns]:
        messages.append(Message(role="user", content=turn.user_message))
        response_text = _send_with_retries(
            model=model,
            messages=messages,
            system=config.system_prompt,
            retries=config.retries,
        )
        judge = score_turn_rules(turn.user_message, response_text)
        turn_result = TurnResult(
            turn_index=turn.turn_index,
            user_message=turn.user_message,
            expected_handling=turn.expected_handling.value,
            expected_rationale=turn.rationale,
            model_response=response_text,
            handling_label=judge.turn_label,
            scoring_rationale=judge.rationale,
        )
        turn_results.append(turn_result)
        messages.append(Message(role="assistant", content=response_text))

        if config.early_stop_on_refusal and judge.turn_label in {
            TurnLabel.SOFT_REFUSE,
            TurnLabel.HARD_REFUSE,
        }:
            stopped_early = True
            stopped_at_turn = turn.turn_index
            refusal_text = response_text
            break

    labels = [turn.handling_label for turn in turn_results]
    trajectory_label = score_trajectory(labels)
    assessment = assess_outcome(
        trajectory.expected_trajectory_outcome.value,
        labels,
        trajectory_label,
    )
    return TrajectoryResult(
        trajectory_id=trajectory.id,
        proxy_domain=trajectory.proxy_domain.value,
        difficulty=trajectory.difficulty.value,
        shape_of_real_workflow=trajectory.shape_of_real_workflow,
        trajectory_level_concern=trajectory.trajectory_level_concern,
        expected_trajectory_outcome=trajectory.expected_trajectory_outcome.value,
        model_id=model.model_id,
        run_started_at=datetime.now(timezone.utc).isoformat(),
        config=asdict(config),
        turns=turn_results,
        trajectory_label=trajectory_label,
        expectation_met=assessment.expectation_met,
        failure_mode=assessment.failure_mode,
        first_restrictive_turn=assessment.first_restrictive_turn,
        stopped_early=stopped_early,
        stopped_at_turn=stopped_at_turn,
        refusal_text=refusal_text,
    )
