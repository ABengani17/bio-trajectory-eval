# Methodology

## Measurement Target

Protocol Signal Eval measures model reliability on lab-automation-adjacent protocol work. The unit of analysis is a structured artifact, not a chat answer.

A useful model should:

- preserve user constraints across turns
- represent protocol intent in machine-readable JSON
- identify missing execution-readiness information
- catch seeded defects in drafts and plate maps
- produce valid worklist rows for safe fixtures
- distinguish safe review support from execution guidance
- flag screening, provenance, approval, or biosafety review checkpoints when the fixture mentions constructs or unknown samples

The harness does not evaluate real biological success or hazard. It evaluates whether the model creates reviewable protocol artifacts under safe conditions.

## Fixture Design

All fixtures use non-hazardous substitutes: colored water, food dye, mock buffers, dummy sample IDs, and synthetic plate maps. Screening checkpoint tasks reference missing metadata, not real sequences.

This keeps the repo useful for protocol-assistant engineering without distributing operational biological instructions.

## Task Families

`protocol_intake` tasks start from messy natural language and expect a structured intent object. The scorer checks required fields, assumptions, and clarifying questions.

`protocol_review` tasks provide flawed drafts with seeded defects. The scorer measures recall over known issue codes and tracks extra findings as false positives.

`worklist_generation` tasks ask for small safe transfer tables. The scorer checks well coordinates, volumes, duplicate destinations, and row structure.

`trajectory_refinement` tasks simulate multi-turn edits. The scorer checks whether the final artifact, change log, contradictions, assumptions, and clarifying questions are present.

`screening_checkpoint` tasks mention constructs, external vendors, or unknown samples. The expected behavior is non-operational: require screening/provenance/approval gates and avoid build or execution instructions.

## Interpretation

Scores are triage signals. A high score means the artifact passed deterministic checks for the fixture. A low score points to concrete failure modes: missing fields, missed seeded issues, invalid worklist rows, or missing checkpoints.

Human review remains important. The deterministic checks are intentionally transparent so failures can be inspected quickly and added back into the fixture set.
