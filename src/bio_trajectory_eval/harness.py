from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from bio_trajectory_eval.adapters.base import Message, ModelAdapter
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
    model_response: str
    handling_label: TurnLabel
    scoring_rationale: str


@dataclass(frozen=True)
class TrajectoryResult:
    trajectory_id: str
    proxy_domain: str
    difficulty: str
    model_id: str
    run_started_at: str
    config: dict
    turns: list[TurnResult]
    trajectory_label: TrajectoryLabel
    stopped_early: bool
    stopped_at_turn: int | None
    refusal_text: str | None

    def to_json_dict(self) -> dict:
        data = asdict(self)
        data["trajectory_label"] = self.trajectory_label.value
        for turn in data["turns"]:
            turn["handling_label"] = turn["handling_label"].value
        return data


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
        response = model.send(messages=messages, system=config.system_prompt)
        judge = score_turn_rules(turn.user_message, response.content)
        turn_result = TurnResult(
            turn_index=turn.turn_index,
            user_message=turn.user_message,
            model_response=response.content,
            handling_label=judge.turn_label,
            scoring_rationale=judge.rationale,
        )
        turn_results.append(turn_result)
        messages.append(Message(role="assistant", content=response.content))

        if config.early_stop_on_refusal and judge.turn_label in {
            TurnLabel.SOFT_REFUSE,
            TurnLabel.HARD_REFUSE,
        }:
            stopped_early = True
            stopped_at_turn = turn.turn_index
            refusal_text = response.content
            break

    labels = [turn.handling_label for turn in turn_results]
    return TrajectoryResult(
        trajectory_id=trajectory.id,
        proxy_domain=trajectory.proxy_domain.value,
        difficulty=trajectory.difficulty.value,
        model_id=model.model_id,
        run_started_at=datetime.now(timezone.utc).isoformat(),
        config=asdict(config),
        turns=turn_results,
        trajectory_label=score_trajectory(labels),
        stopped_early=stopped_early,
        stopped_at_turn=stopped_at_turn,
        refusal_text=refusal_text,
    )
