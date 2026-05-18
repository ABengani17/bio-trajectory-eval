# Methodology

The scanner is rule-based. It loads a manifest, optionally merges Opentrons protocol metadata, runs checks, and returns findings with stable `code` values and severities.

## Inputs

Manifest fields mirror data that often already exists in LIMS, request forms, inventory, and protocol exports: platform, samples, transfers, controls, approvals, and decontamination plan.

## Policy

The same manifest can pass under one policy and block under another. Policy JSON sets material lists, thresholds, labware geometry, and optional `finding_actions` overrides.

## Decisions

| Decision | Rule |
| --- | --- |
| `pass` | No medium, high, or critical findings (and no policy override to review/block) |
| `review` | Medium or high findings, or a `require_review` override |
| `block` | Critical findings, or a `block_run` override |

## Scope

Metadata readiness only. No sequence analysis, protocol execution, or liquid-handling simulation.

Typical use: call `BiosecurityGate` from a labbench Rack before scheduling; stop or route to a reviewer when the decision is not `pass`.
