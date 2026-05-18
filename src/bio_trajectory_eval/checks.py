from __future__ import annotations

import re
from collections import Counter

from bio_trajectory_eval.schema import (
    AutomationPackage,
    Decision,
    Finding,
    FindingAction,
    MaterialType,
    Platform,
    Policy,
    ScanResult,
    ScanSummary,
    ScreeningStatus,
    Severity,
)


BIOLOGICAL_MATERIALS = {
    MaterialType.SYNTHETIC_DNA,
    MaterialType.CONTROLLED_CONSTRUCT,
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


def _valid_well(value: str, rows: str, columns: int) -> bool:
    pattern = re.compile(rf"^([{re.escape(rows)}])([1-9][0-9]*)$")
    match = pattern.match(value.upper())
    return bool(match and 1 <= int(match.group(2)) <= columns)


def _scan_metadata(package: AutomationPackage, policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    if package.platform == Platform.OPENTRONS:
        if policy.require_opentrons_api_level and not package.metadata.api_level:
            findings.append(
                finding(
                    "missing_opentrons_api_level",
                    Severity.MEDIUM,
                    "metadata.api_level",
                    "Opentrons package does not declare an API level.",
                    "Add apiLevel through Opentrons metadata or requirements before review.",
                )
            )
        if policy.require_protocol_name and not package.metadata.protocol_name:
            findings.append(
                finding(
                    "missing_protocol_name",
                    Severity.LOW,
                    "metadata.protocol_name",
                    "Protocol name is missing from package metadata.",
                    "Add a stable protocol name for audit and run traceability.",
                )
            )
    if package.platform == Platform.AUTOPROTOCOL and policy.require_protocol_name and not package.metadata.protocol_name:
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


def _scan_samples(package: AutomationPackage, policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    for index, sample in enumerate(package.samples):
        path = f"samples[{index}]"
        if sample.material_type == MaterialType.UNKNOWN:
            findings.append(
                finding(
                    "unknown_material_type",
                    Severity.CRITICAL if policy.block_on_unknown_material else Severity.HIGH,
                    f"{path}.material_type",
                    f"Sample {sample.id} has unknown material type.",
                    "Classify the material before scheduling automation.",
                )
            )
        requires_provenance = sample.material_type in BIOLOGICAL_MATERIALS
        if policy.require_provenance_for_external_materials and sample.external:
            requires_provenance = True
        if requires_provenance and not sample.provenance_id:
            findings.append(
                finding(
                    "missing_provenance",
                    Severity.HIGH,
                    f"{path}.provenance_id",
                    f"Sample {sample.id} is biological or unknown but has no provenance record.",
                    "Attach source, owner, and chain-of-custody metadata before review.",
                )
            )
        if sample.material_type in set(policy.require_sequence_screening_for):
            if sample.screening_status == ScreeningStatus.PENDING:
                findings.append(
                    finding(
                        "sequence_screening_pending",
                        Severity.HIGH,
                        f"{path}.screening_status",
                        f"Sample {sample.id} has screening in progress.",
                        "Wait for the screening provider result or attach screening_record_id when passed.",
                    )
                )
            elif sample.screening_status != ScreeningStatus.PASSED or not sample.screening_record_id:
                findings.append(
                    finding(
                        "missing_sequence_screening",
                        Severity.CRITICAL if policy.block_on_missing_sequence_screening else Severity.HIGH,
                        f"{path}.screening_status",
                        f"Sample {sample.id} requires a passed screening record.",
                        "Attach screening status, screening_record_id, and screening_provider (e.g. IGSC vendor ID, commec run ID) before release.",
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
        if sample.material_type in set(policy.require_biosafety_review_for):
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


def _scan_transfers(package: AutomationPackage, policy: Policy) -> list[Finding]:
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
        labware = policy.default_labware
        if not _valid_well(transfer.source_well, labware.rows, labware.columns):
            findings.append(
                finding(
                    "invalid_source_well",
                    Severity.MEDIUM,
                    f"{path}.source_well",
                    f"Source well {transfer.source_well} is not valid for {labware.name}.",
                    "Correct the source well or configure the labware rule for this package.",
                )
            )
        if not _valid_well(transfer.dest_well, labware.rows, labware.columns):
            findings.append(
                finding(
                    "invalid_destination_well",
                    Severity.MEDIUM,
                    f"{path}.dest_well",
                    f"Destination well {transfer.dest_well} is not valid for {labware.name}.",
                    "Correct the destination well or configure the labware rule for this package.",
                )
            )
        destinations[transfer.dest_well.upper()] += 1
        if transfer.volume_ul > policy.max_transfer_ul_without_review:
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
    if len(package.transfers) > policy.high_throughput_transfer_count and not package.approvals:
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


def _scan_package_controls(package: AutomationPackage, policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    has_bioactive = any(sample.material_type in BIOLOGICAL_MATERIALS for sample in package.samples)
    if policy.require_decontamination_for_biological_materials and has_bioactive and not package.decontamination_plan:
        findings.append(
            finding(
                "missing_decontamination_plan",
                Severity.HIGH,
                "decontamination_plan",
                "Package includes biological or unknown materials but no decontamination plan.",
                "Attach the relevant waste handling and deck cleanup plan before scheduling.",
            )
        )
    if policy.require_controls_for_biological_materials and has_bioactive and not package.controls:
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


def decision_for(findings: list[Finding], policy: Policy | None = None) -> Decision:
    if policy is not None:
        actions = [policy.finding_actions.get(item.code) for item in findings]
        if FindingAction.BLOCK_RUN in actions:
            return Decision.BLOCK
        if FindingAction.REQUIRE_REVIEW in actions:
            return Decision.REVIEW
    severities = {item.severity for item in findings}
    if Severity.CRITICAL in severities:
        return Decision.BLOCK
    if Severity.HIGH in severities or Severity.MEDIUM in severities:
        return Decision.REVIEW
    return Decision.PASS


def scan_package(package: AutomationPackage, policy: Policy | None = None) -> ScanResult:
    policy = policy or Policy()
    findings = []
    findings.extend(_scan_metadata(package, policy))
    findings.extend(_scan_samples(package, policy))
    findings.extend(_scan_transfers(package, policy))
    findings.extend(_scan_package_controls(package, policy))

    counts = Counter(item.severity for item in findings)
    summary = ScanSummary(
        package_id=package.id,
        platform=package.platform,
        policy_name=policy.name,
        decision=decision_for(findings, policy),
        finding_count=len(findings),
        critical_count=counts[Severity.CRITICAL],
        high_count=counts[Severity.HIGH],
        medium_count=counts[Severity.MEDIUM],
    )
    return ScanResult(summary=summary, findings=findings)
