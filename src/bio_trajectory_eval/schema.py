from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProxyDomain(StrEnum):
    CROP_PATHOGEN_DEFENSE = "crop_pathogen_defense"
    MOLECULAR_BIOLOGY_PEDAGOGY = "molecular_biology_pedagogy"
    LAB_AUTOMATION = "lab_automation"


class Difficulty(StrEnum):
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"


class ExpectedHandling(StrEnum):
    ANSWER_FREELY = "answer_freely"
    ANSWER_WITH_CAVEATS = "answer_with_caveats"
    SOFT_REFUSE = "soft_refuse"
    HARD_REFUSE = "hard_refuse"


class ExpectedTrajectoryOutcome(StrEnum):
    ANSWER_THROUGHOUT = "answer_throughout"
    REDIRECT_BY_FINAL_TURN = "redirect_by_final_turn"
    REFUSE_OR_REDIRECT_BY_TURN_2 = "refuse_or_redirect_by_turn_2"
    REFUSE_OR_REDIRECT_BY_TURN_3 = "refuse_or_redirect_by_turn_3"


class TrajectoryTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turn_index: int = Field(ge=0)
    user_message: str = Field(min_length=1)
    expected_handling: ExpectedHandling
    rationale: str = Field(min_length=1)


class Trajectory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^traj_[0-9]{4}$")
    proxy_domain: ProxyDomain
    shape_of_real_workflow: str = Field(min_length=1)
    difficulty: Difficulty
    turns: list[TrajectoryTurn] = Field(min_length=2)
    trajectory_level_concern: str = Field(min_length=1)
    expected_trajectory_outcome: ExpectedTrajectoryOutcome
    notes: str = ""

    @field_validator("turns")
    @classmethod
    def turn_indices_are_contiguous(cls, turns: list[TrajectoryTurn]) -> list[TrajectoryTurn]:
        expected = list(range(len(turns)))
        observed = [turn.turn_index for turn in turns]
        if observed != expected:
            raise ValueError(f"turn_index values must be contiguous from zero, got {observed}")
        return turns

    @model_validator(mode="after")
    def outcome_matches_tier(self) -> "Trajectory":
        if self.difficulty == Difficulty.TIER_1:
            if self.expected_trajectory_outcome != ExpectedTrajectoryOutcome.ANSWER_THROUGHOUT:
                raise ValueError("tier_1 trajectories must expect answer_throughout")
        if self.difficulty == Difficulty.TIER_3:
            early = {
                ExpectedTrajectoryOutcome.REFUSE_OR_REDIRECT_BY_TURN_2,
                ExpectedTrajectoryOutcome.REFUSE_OR_REDIRECT_BY_TURN_3,
            }
            if self.expected_trajectory_outcome not in early:
                raise ValueError("tier_3 trajectories must expect an early redirect")
        return self


def load_trajectories(path: str | Path) -> list[Trajectory]:
    trajectories: list[Trajectory] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                raw = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_number}: {exc}") from exc
            try:
                trajectories.append(Trajectory.model_validate(raw))
            except Exception as exc:
                raise ValueError(f"invalid trajectory on line {line_number}: {exc}") from exc
    return trajectories
