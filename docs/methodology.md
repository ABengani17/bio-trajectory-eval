# Methodology

`bio-trajectory-eval` treats a lab automation run as a package that should not be scheduled until key biosecurity and operations records are present.

The scanner is rule-based and policy-driven. It reads a manifest, optionally extracts Opentrons protocol metadata, and emits findings with stable codes, severity, location, message, and recommendation. In labbench workflows, the scanner is exposed as `BiosecurityGate`, a virtual device that can run before instruments are opened.

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

## Policy

The same manifest can be acceptable in one context and blocked in another. The policy file captures local choices such as:

- whether unknown materials block or route to review
- which material types require sequence-screening records
- which material types require biosafety review
- whether missing biosafety review is a high finding or a hard block
- transfer-count and transfer-volume thresholds
- labware geometry used for well validation

## Decisions

`pass` means no medium, high, or critical findings were detected.

`review` means the package has medium or high findings that need human review before scheduling.

`block` means at least one critical finding is present. Current critical findings include missing screening records for synthetic DNA or controlled constructs and missing biosafety review for unknown materials.

## Scope

The scanner checks metadata readiness. It does not screen sequences, execute protocol code, simulate liquid handling, or make scientific validity decisions.

The useful deployment pattern is to run the gate as part of automation orchestration: if it passes, the automation script can proceed; if it returns review or block, scheduling is stopped or routed to a reviewer with an audit record.
