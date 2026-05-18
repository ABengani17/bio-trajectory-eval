from __future__ import annotations

import re
from collections import Counter

from bio_trajectory_eval.schema import (
    AutomationPackage,
    Decision,
    Finding,
    MaterialType,
    Platform,
    ScanResult,
    ScanSummary,
    ScreeningStatus,
    Severity,
)


WELL_RE = re.compile(r"^([A-H])([1-9]|1[0-2])$")
BIOLOGICAL_MATERIALS = {
    MaterialType.SYNTHETIC_DNA,
    MaterialType.CONTROLLED_CONSTRUCT,
    MaterialType.ORGANISM,
    MaterialType.CELL_LINE,
    MaterialType.CLINICAL_SAMPLE,
    MaterialType.ENVIRONMENTAL_SAMPLE,
    MaterialType.UNKNOWN,
}
SCREENING_MATERIALS = {
    MaterialType.SYNTHETIC_DNA,
    MaterialType.CONTROLLED_CONSTRUCT,
}
BIOSAFETY_REVIEW_MATERIALS = {
    MaterialType.ORGANISM,
    MaterialType.CELL_LINE,
    MaterialType.CLINICAL_SAMPLE,
    MaterialType.ENVIRONMENTAL_SAMPLE,
    MaterialType.UNKNOWN,
}


def finding(code: str, severity: Severity, path: str, message: str, recommendation: str) -> Finding:
    return Finding(
        code=code,
        severity=severity,
        path=path,
        message=message,
        recommendation=recommendation,
    )


def _valid_well(value: str) -> bool:
    return bool(WELL_RE.match(value.upper()))


def _scan_metadata(package: AutomationPackage) -> list[Finding]:
    findings: list[Finding] = []
    if package.platform == Platform.OPENTRONS:
        if not package.metadata.api_level:
            findings.append(
                finding(
                    "missing_opentrons_api_level",
                    Severity.MEDIUM,
                    "metadata.api_level",
                    "Opentrons package does not declare an API level.",
                    "Add apiLevel through Opentrons metadata or requirements before review.",
                )
            )
        if not package.metadata.protocol_name:
            findings.append(
                finding(
                    "missing_protocol_name",
                    Severity.LOW,
                    "metadata.protocol_name",
                    "Protocol name is missing from package metadata.",
                    "Add a stable protocol name for audit and run traceability.",
                )
            )
    if package.platform == Platform.AUTOPROTOCOL and not package.metadata.protocol_name:
        findings.append(
            finding(
                "missing_protocol_name",
                Severity.LOW,
                "metadata.protocol_name",
                "Autoprotocol package does not include a protocol name.",
                "Add a stable protocol name before routing for review.",
            )
        )
    return findings


def _scan_samples(package: AutomationPackage) -> list[Finding]:
    findings: list[Finding] = []
    for index, sample in enumerate(package.samples):
        path = f"samples[{index}]"
        if sample.material_type == MaterialType.UNKNOWN:
            findings.append(
                finding(
                    "unknown_material_type",
                    Severity.HIGH,
                    f"{path}.material_type",
                    f"Sample {sample.id} has unknown material type.",
                    "Classify the material before scheduling automation.",
                )
            )
        if sample.material_type in BIOLOGICAL_MATERIALS and not sample.provenance_id:
            findings.append(
                finding(
                    "missing_provenance",
                    Severity.HIGH,
                    f"{path}.provenance_id",
                    f"Sample {sample.id} is biological or unknown but has no provenance record.",
                    "Attach source, owner, and chain-of-custody metadata before review.",
                )
            )
        if sample.material_type in SCREENING_MATERIALS:
            if sample.screening_status != ScreeningStatus.PASSED or not sample.screening_record_id:
                findings.append(
                    finding(
                        "missing_sequence_screening",
                        Severity.CRITICAL,
                        f"{path}.screening_status",
                        f"Sample {sample.id} requires a passed screening record.",
                        "Attach screening status and record ID before the package can be released.",
                    )
                )
            if not sample.approval_id:
                findings.append(
                    finding(
                        "missing_construct_approval",
                        Severity.HIGH,
                        f"{path}.approval_id",
                        f"Sample {sample.id} is synthetic or controlled and lacks approval metadata.",
                        "Attach the internal approval or order review ID.",
                    )
                )
        if sample.material_type in BIOSAFETY_REVIEW_MATERIALS:
            if not sample.biosafety_review_id:
                findings.append(
                    finding(
                        "missing_biosafety_review",
                        Severity.CRITICAL if sample.material_type == MaterialType.UNKNOWN else Severity.HIGH,
                        f"{path}.biosafety_review_id",
                        f"Sample {sample.id} requires biosafety review metadata.",
                        "Route the package to biosafety review before scheduling.",
                    )
                )
        if sample.biosafety_level >= 2 and not sample.approval_id:
            findings.append(
                finding(
                    "missing_bsl_approval",
                    Severity.HIGH,
                    f"{path}.approval_id",
                    f"Sample {sample.id} is BSL-{sample.biosafety_level} but lacks approval metadata.",
                    "Attach the approved protocol or authorization ID.",
                )
            )
    return findings


def _scan_transfers(package: AutomationPackage) -> list[Finding]:
    findings: list[Finding] = []
    sample_ids = {sample.id for sample in package.samples}
    destinations: Counter[str] = Counter()
    for index, transfer in enumerate(package.transfers):
        path = f"transfers[{index}]"
        if transfer.sample_id not in sample_ids:
            findings.append(
                finding(
                    "undeclared_sample_transfer",
                    Severity.HIGH,
                    f"{path}.sample_id",
                    f"Transfer references undeclared sample {transfer.sample_id}.",
                    "Declare every transferred sample in the package manifest.",
                )
            )
        if not _valid_well(transfer.source_well):
            findings.append(
                finding(
                    "invalid_source_well",
                    Severity.MEDIUM,
                    f"{path}.source_well",
                    f"Source well {transfer.source_well} is not valid for a 96-well plate.",
                    "Correct the source well or declare compatible labware in a future schema version.",
                )
            )
        if not _valid_well(transfer.dest_well):
            findings.append(
                finding(
                    "invalid_destination_well",
                    Severity.MEDIUM,
                    f"{path}.dest_well",
                    f"Destination well {transfer.dest_well} is not valid for a 96-well plate.",
                    "Correct the destination well or declare compatible labware in a future schema version.",
                )
            )
        destinations[transfer.dest_well.upper()] += 1
        if transfer.volume_ul > 1000:
            findings.append(
                finding(
                    "large_transfer_volume",
                    Severity.LOW,
                    f"{path}.volume_ul",
                    f"Transfer volume {transfer.volume_ul:g} uL is unusually large for plate automation.",
                    "Confirm labware capacity and split the transfer if needed.",
                )
            )
    for well, count in destinations.items():
        if count > 1:
            findings.append(
                finding(
                    "reused_destination_well",
                    Severity.LOW,
                    "transfers",
                    f"Destination well {well} appears in {count} transfers.",
                    "Confirm pooling is intentional or split destination wells.",
                )
            )
    if len(package.transfers) > 96 and not package.approvals:
        findings.append(
            finding(
                "high_throughput_without_approval",
                Severity.MEDIUM,
                "approvals",
                "Package has more than 96 transfers and no approval metadata.",
                "Attach batch approval or reviewer signoff for high-throughput automation.",
            )
        )
    return findings


def _scan_package_controls(package: AutomationPackage) -> list[Finding]:
    findings: list[Finding] = []
    has_bioactive = any(sample.material_type in BIOLOGICAL_MATERIALS for sample in package.samples)
    if has_bioactive and not package.decontamination_plan:
        findings.append(
            finding(
                "missing_decontamination_plan",
                Severity.HIGH,
                "decontamination_plan",
                "Package includes biological or unknown materials but no decontamination plan.",
                "Attach the relevant waste handling and deck cleanup plan before scheduling.",
            )
        )
    if has_bioactive and not package.controls:
        findings.append(
            finding(
                "missing_controls",
                Severity.MEDIUM,
                "controls",
                "Package includes biological or unknown materials but no controls are declared.",
                "Declare negative, positive, blank, or process controls as appropriate for review.",
            )
        )
    return findings


def decision_for(findings: list[Finding]) -> Decision:
    severities = {item.severity for item in findings}
    if Severity.CRITICAL in severities:
        return Decision.BLOCK
    if Severity.HIGH in severities or Severity.MEDIUM in severities:
        return Decision.REVIEW
    return Decision.PASS


def scan_package(package: AutomationPackage) -> ScanResult:
    findings = []
    findings.extend(_scan_metadata(package))
    findings.extend(_scan_samples(package))
    findings.extend(_scan_transfers(package))
    findings.extend(_scan_package_controls(package))

    counts = Counter(item.severity for item in findings)
    summary = ScanSummary(
        package_id=package.id,
        platform=package.platform,
        decision=decision_for(findings),
        finding_count=len(findings),
        critical_count=counts[Severity.CRITICAL],
        high_count=counts[Severity.HIGH],
        medium_count=counts[Severity.MEDIUM],
    )
    return ScanResult(summary=summary, findings=findings)
