from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskType(StrEnum):
    PROTOCOL_INTAKE = "protocol_intake"
    PROTOCOL_REVIEW = "protocol_review"
    WORKLIST_GENERATION = "worklist_generation"
    TRAJECTORY_REFINEMENT = "trajectory_refinement"
    SCREENING_CHECKPOINT = "screening_checkpoint"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SeededIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(pattern=r"^[a-z0-9_]+$")
    severity: Severity
    description: str = Field(min_length=1)
    evidence_hint: str = Field(min_length=1)


class ExpectedSignals(BaseModel):
    model_config = ConfigDict(extra="forbid")

    required_fields: list[str] = Field(default_factory=list)
    seeded_issues: list[SeededIssue] = Field(default_factory=list)
    required_checkpoints: list[str] = Field(default_factory=list)
    forbidden_patterns: list[str] = Field(default_factory=list)
    max_transfer_ul: float | None = Field(default=None, gt=0)
    allowed_well_rows: str = "ABCDEFGH"
    allowed_well_columns: int = Field(default=12, ge=1, le=48)


class ProtocolTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^task_[0-9]{4}$")
    task_type: TaskType
    title: str = Field(min_length=1)
    intent: str = Field(min_length=1)
    input: dict[str, Any] = Field(default_factory=dict)
    expected: ExpectedSignals = Field(default_factory=ExpectedSignals)
    notes: str = ""

    @field_validator("input")
    @classmethod
    def input_is_nonempty(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not value:
            raise ValueError("input must contain the task fixture")
        return value


def load_tasks(path: str | Path) -> list[ProtocolTask]:
    tasks: list[ProtocolTask] = []
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
                tasks.append(ProtocolTask.model_validate(raw))
            except Exception as exc:
                raise ValueError(f"invalid task on line {line_number}: {exc}") from exc
    return tasks
