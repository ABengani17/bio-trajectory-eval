# Methodology

`bio-trajectory-eval` treats a lab automation run as a package that should not be scheduled until key biosecurity and operations records are present.

The scanner is rule-based. It reads a manifest, optionally extracts Opentrons protocol metadata, and emits findings with stable codes, severity, location, message, and recommendation.

## Inputs

The manifest captures:

- automation platform
- protocol metadata
- samples and material types
- provenance and screening records
- biosafety and approval identifiers
- transfers
- controls
- decontamination plan

This is intentionally close to fields that already exist in LIMS, request forms, inventory systems, Opentrons protocol metadata, Autoprotocol descriptions, and worklist exports.

## Decisions

`pass` means no medium, high, or critical findings were detected.

`review` means the package has medium or high findings that need human review before scheduling.

`block` means at least one critical finding is present. Current critical findings include missing screening records for synthetic DNA or controlled constructs and missing biosafety review for unknown materials.

## Scope

The scanner checks metadata readiness. It does not screen sequences, execute protocol code, simulate liquid handling, or make scientific validity decisions.
