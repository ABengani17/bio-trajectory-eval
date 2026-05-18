from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Platform(StrEnum):
    OPENTRONS = "opentrons"
    AUTOPROTOCOL = "autoprotocol"
    WORKLIST = "worklist"
    OTHER = "other"


class MaterialType(StrEnum):
    INERT = "inert"
    BUFFER = "buffer"
    REAGENT = "reagent"
    SYNTHETIC_DNA = "synthetic_dna"
    CONTROLLED_CONSTRUCT = "controlled_construct"
    ORGANISM = "organism"
    CELL_LINE = "cell_line"
    CLINICAL_SAMPLE = "clinical_sample"
    ENVIRONMENTAL_SAMPLE = "environmental_sample"
    UNKNOWN = "unknown"


class ScreeningStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    PASSED = "passed"
    PENDING = "pending"
    MISSING = "missing"


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Decision(StrEnum):
    PASS = "pass"
    REVIEW = "review"
    BLOCK = "block"


class FindingAction(StrEnum):
    RECORD_ONLY = "record_only"
    REQUIRE_REVIEW = "require_review"
    BLOCK_RUN = "block_run"


class Sample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    material_type: MaterialType
    source: str = ""
    provenance_id: str = ""
    screening_status: ScreeningStatus = ScreeningStatus.NOT_REQUIRED
    screening_record_id: str = ""
    approval_id: str = ""
    biosafety_review_id: str = ""
    biosafety_level: int = Field(default=1, ge=1, le=4)
    external: bool = False


class Transfer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(min_length=1)
    source_well: str = Field(min_length=1)
    dest_well: str = Field(min_length=1)
    volume_ul: float = Field(gt=0)


class ProtocolMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    protocol_name: str = ""
    author: str = ""
    api_level: str = ""
    robot_type: str = ""


class AutomationPackage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[A-Za-z0-9_.-]+$")
    name: str = Field(min_length=1)
    platform: Platform
    protocol_file: str = ""
    metadata: ProtocolMetadata = Field(default_factory=ProtocolMetadata)
    samples: list[Sample] = Field(default_factory=list)
    transfers: list[Transfer] = Field(default_factory=list)
    controls: list[str] = Field(default_factory=list)
    approvals: list[str] = Field(default_factory=list)
    decontamination_plan: str = ""
    notes: str = ""

    @field_validator("samples")
    @classmethod
    def sample_ids_are_unique(cls, samples: list[Sample]) -> list[Sample]:
        ids = [sample.id for sample in samples]
        if len(ids) != len(set(ids)):
            raise ValueError("sample ids must be unique")
        return samples


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(pattern=r"^[a-z0-9_]+$")
    severity: Severity
    path: str
    message: str
    recommendation: str


class ScanSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    package_id: str
    platform: Platform
    policy_name: str
    decision: Decision
    finding_count: int
    critical_count: int
    high_count: int
    medium_count: int
    checked_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ScanResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: ScanSummary
    findings: list[Finding]


class LabwareRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    rows: str = "ABCDEFGH"
    columns: int = Field(default=12, ge=1, le=48)
    max_well_volume_ul: float | None = Field(default=None, gt=0)


class Policy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = "default"
    require_opentrons_api_level: bool = True
    require_protocol_name: bool = True
    require_controls_for_biological_materials: bool = True
    require_decontamination_for_biological_materials: bool = True
    require_provenance_for_external_materials: bool = True
    require_sequence_screening_for: list[MaterialType] = Field(
        default_factory=lambda: [MaterialType.SYNTHETIC_DNA, MaterialType.CONTROLLED_CONSTRUCT]
    )
    require_biosafety_review_for: list[MaterialType] = Field(
        default_factory=lambda: [
            MaterialType.ORGANISM,
            MaterialType.CELL_LINE,
            MaterialType.CLINICAL_SAMPLE,
            MaterialType.ENVIRONMENTAL_SAMPLE,
            MaterialType.UNKNOWN,
        ]
    )
    block_on_unknown_material: bool = False
    block_on_missing_sequence_screening: bool = True
    max_transfer_ul_without_review: float = Field(default=1000, gt=0)
    high_throughput_transfer_count: int = Field(default=96, ge=1)
    default_labware: LabwareRule = Field(default_factory=lambda: LabwareRule(name="96_well_plate"))
    finding_actions: dict[str, FindingAction] = Field(default_factory=dict)


def load_package(path: str | Path) -> AutomationPackage:
    with Path(path).open("r", encoding="utf-8") as handle:
        raw: dict[str, Any] = json.load(handle)
    try:
        return AutomationPackage.model_validate(raw)
    except Exception as exc:
        raise ValueError(f"invalid automation package {path}: {exc}") from exc


def load_policy(path: str | Path | None = None) -> Policy:
    if path is None:
        return Policy()
    with Path(path).open("r", encoding="utf-8") as handle:
        raw: dict[str, Any] = json.load(handle)
    try:
        return Policy.model_validate(raw)
    except Exception as exc:
        raise ValueError(f"invalid policy {path}: {exc}") from exc


def dump_json(data: BaseModel) -> str:
    return json.dumps(data.model_dump(mode="json"), indent=2, sort_keys=True)
