# Methodology

The scanner is rule-based and policy-driven. It validates manifest structure, then applies checks in four groups: protocol metadata, samples, transfers, and package-level controls/cleanup.

## Alignment with common biosecurity practice

| Practice | How this repo supports it |
| --- | --- |
| IGSC-style sequence screening before release | Requires `screening_status: passed` and `screening_record_id` for configured material types; flags `pending` |
| Chain of custody for external samples | `provenance_id` + `external` |
| Institutional biosafety review | `biosafety_review_id` for configured material types |
| Run authorization | `approval_id`, package `approvals` |
| Automation traceability | Opentrons metadata, undeclared transfer detection, audit log |

Sequence analysis itself is out of scope; see [integration.md](integration.md).

## Decisions

See [policy.md](policy.md) and [problems_and_solutions.md](problems_and_solutions.md).

## Scope

Metadata and policy only. No protocol execution, no BLAST/HMM screening, no deck physics simulation.
