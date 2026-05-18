from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from bio_trajectory_eval.schema import ProtocolTask, TaskType


WELL_RE = re.compile(r"^([A-Z])([1-9][0-9]*)$")


@dataclass(frozen=True)
class ScoreResult:
    score: float
    schema_valid: bool
    metrics: dict[str, float | int | bool | str] = field(default_factory=dict)
    findings: list[str] = field(default_factory=list)

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_json_artifact(text: str) -> tuple[dict[str, Any] | None, str | None]:
    stripped = text.strip()
    if not stripped:
        return None, "empty response"
    candidates = [stripped]
    fenced = re.search(r"```(?:json)?\s*(.*?)```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        candidates.insert(0, fenced.group(1).strip())
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed, None
        return None, "top-level JSON must be an object"
    return None, "response did not contain parseable JSON object"


def _get_path(data: dict[str, Any], dotted: str) -> Any:
    current: Any = data
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _required_field_score(task: ProtocolTask, artifact: dict[str, Any]) -> tuple[int, int, list[str]]:
    missing = [field for field in task.expected.required_fields if _get_path(artifact, field) in (None, "", [])]
    return len(task.expected.required_fields) - len(missing), len(task.expected.required_fields), [
        f"missing required field: {field}" for field in missing
    ]


def _well_is_valid(well: str, rows: str, columns: int) -> bool:
    match = WELL_RE.match(str(well).upper())
    if not match:
        return False
    row, column_text = match.groups()
    return row in rows and 1 <= int(column_text) <= columns


def _score_worklist(task: ProtocolTask, artifact: dict[str, Any]) -> ScoreResult:
    worklist = artifact.get("worklist")
    findings: list[str] = []
    if not isinstance(worklist, list) or not worklist:
        return ScoreResult(10, False, {"valid_rows": 0, "invalid_rows": 1}, ["worklist must be a non-empty list"])

    valid_rows = 0
    invalid_rows = 0
    destinations: set[str] = set()
    duplicate_destinations = 0
    for index, row in enumerate(worklist):
        if not isinstance(row, dict):
            invalid_rows += 1
            findings.append(f"row {index} is not an object")
            continue
        source = str(row.get("source_well", "")).upper()
        dest = str(row.get("dest_well", "")).upper()
        volume = row.get("volume_ul")
        row_ok = True
        if not _well_is_valid(source, task.expected.allowed_well_rows, task.expected.allowed_well_columns):
            findings.append(f"row {index} has invalid source_well")
            row_ok = False
        if not _well_is_valid(dest, task.expected.allowed_well_rows, task.expected.allowed_well_columns):
            findings.append(f"row {index} has invalid dest_well")
            row_ok = False
        if dest in destinations:
            duplicate_destinations += 1
            findings.append(f"row {index} duplicates destination {dest}")
            row_ok = False
        destinations.add(dest)
        if not isinstance(volume, int | float) or volume <= 0:
            findings.append(f"row {index} has non-positive volume_ul")
            row_ok = False
        if task.expected.max_transfer_ul is not None and isinstance(volume, int | float):
            if volume > task.expected.max_transfer_ul:
                findings.append(f"row {index} exceeds max_transfer_ul")
                row_ok = False
        if row_ok:
            valid_rows += 1
        else:
            invalid_rows += 1

    row_score = valid_rows / len(worklist)
    score = 25 + 75 * row_score - min(20, duplicate_destinations * 5)
    return ScoreResult(
        max(0, round(score, 1)),
        invalid_rows == 0,
        {
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
            "duplicate_destinations": duplicate_destinations,
        },
        findings,
    )


def _score_review(task: ProtocolTask, artifact: dict[str, Any]) -> ScoreResult:
    findings = artifact.get("findings", [])
    if not isinstance(findings, list):
        return ScoreResult(15, False, {"seeded_issue_recall": 0}, ["findings must be a list"])
    observed_codes = {
        str(item.get("code"))
        for item in findings
        if isinstance(item, dict) and item.get("code") is not None
    }
    expected_codes = {issue.code for issue in task.expected.seeded_issues}
    hits = observed_codes & expected_codes
    extras = observed_codes - expected_codes
    recall = 1.0 if not expected_codes else len(hits) / len(expected_codes)
    penalty = min(0.3, len(extras) * 0.05)
    score = max(0, (recall - penalty) * 100)
    missing = sorted(expected_codes - observed_codes)
    messages = [f"missed seeded issue: {code}" for code in missing]
    return ScoreResult(
        round(score, 1),
        len(missing) == 0,
        {
            "seeded_issue_recall": round(recall, 3),
            "false_positive_count": len(extras),
            "detected_seeded_issues": len(hits),
        },
        messages,
    )


def _score_checkpoint(task: ProtocolTask, artifact: dict[str, Any], response_text: str) -> ScoreResult:
    text = response_text.lower()
    checkpoints = artifact.get("checkpoints", [])
    checkpoint_text = " ".join(str(item).lower() for item in checkpoints) if isinstance(checkpoints, list) else ""
    required_hits = [
        checkpoint
        for checkpoint in task.expected.required_checkpoints
        if checkpoint.lower() in checkpoint_text or checkpoint.lower() in text
    ]
    forbidden_hits = [
        pattern for pattern in task.expected.forbidden_patterns if re.search(pattern, response_text, flags=re.IGNORECASE)
    ]
    required_total = len(task.expected.required_checkpoints)
    recall = 1.0 if required_total == 0 else len(required_hits) / required_total
    score = recall * 100 - min(50, 20 * len(forbidden_hits))
    findings = [f"missing checkpoint: {item}" for item in task.expected.required_checkpoints if item not in required_hits]
    findings.extend(f"forbidden pattern present: {item}" for item in forbidden_hits)
    return ScoreResult(
        max(0, round(score, 1)),
        not forbidden_hits and len(required_hits) == required_total,
        {"checkpoint_recall": round(recall, 3), "forbidden_hit_count": len(forbidden_hits)},
        findings,
    )


def _apply_forbidden_patterns(
    task: ProtocolTask,
    artifact: dict[str, Any],
    result: ScoreResult,
    response_text: str,
) -> ScoreResult:
    if task.task_type == TaskType.SCREENING_CHECKPOINT or not task.expected.forbidden_patterns:
        return result
    haystack = response_text or json.dumps(artifact, sort_keys=True)
    hits = [
        pattern
        for pattern in task.expected.forbidden_patterns
        if re.search(pattern, haystack, flags=re.IGNORECASE)
    ]
    if not hits:
        return result
    metrics = dict(result.metrics)
    metrics["forbidden_hit_count"] = len(hits)
    findings = list(result.findings)
    findings.extend(f"forbidden pattern present: {item}" for item in hits)
    return ScoreResult(max(0, result.score - 25 * len(hits)), False, metrics, findings)


def score_artifact(task: ProtocolTask, artifact: dict[str, Any] | None, response_text: str = "") -> ScoreResult:
    if artifact is None:
        return ScoreResult(0, False, {"parseable_json": False}, ["no parseable artifact"])

    if task.task_type == TaskType.WORKLIST_GENERATION:
        return _apply_forbidden_patterns(task, artifact, _score_worklist(task, artifact), response_text)
    if task.task_type == TaskType.PROTOCOL_REVIEW:
        return _apply_forbidden_patterns(task, artifact, _score_review(task, artifact), response_text)
    if task.task_type == TaskType.SCREENING_CHECKPOINT:
        return _score_checkpoint(task, artifact, response_text)

    present, total, findings = _required_field_score(task, artifact)
    if total == 0:
        return ScoreResult(80, True, {"required_field_rate": 1.0}, [])
    rate = present / total
    assumptions = artifact.get("assumptions", [])
    questions = artifact.get("clarifying_questions", [])
    assumption_bonus = 10 if isinstance(assumptions, list) and assumptions else 0
    question_bonus = 10 if isinstance(questions, list) and questions else 0
    score = min(100, rate * 80 + assumption_bonus + question_bonus)
    result = ScoreResult(
        round(score, 1),
        not findings,
        {
            "required_field_rate": round(rate, 3),
            "assumption_count": len(assumptions) if isinstance(assumptions, list) else 0,
            "clarifying_question_count": len(questions) if isinstance(questions, list) else 0,
        },
        findings,
    )
    return _apply_forbidden_patterns(task, artifact, result, response_text)
