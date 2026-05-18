# bio-trajectory-eval

`bio-trajectory-eval` evaluates model outputs for lab-automation protocol review.

The repo is built around a simple question: when a model is asked to help with protocol intake, review, worklist generation, or execution readiness, does it produce a structured artifact that a lab automation team can inspect and score?

It is not a robot runner, a wetlab validator, a synthesis-screening system, or a biological capability benchmark. The current fixtures use safe stand-ins: colored water, food dye, mock buffers, dummy sample IDs, synthetic plate maps, and metadata-only review checkpoints.

## Evaluation Flow

```mermaid
flowchart LR
    A["Task fixture<br/>data/tasks.jsonl"] --> B["Model prompt<br/>artifact contract"]
    B --> C["Model artifact<br/>JSON response"]
    C --> D["Deterministic checks"]
    D --> E["Score + findings<br/>results/*.jsonl"]
    E --> F["Reviewer triage<br/>lowest scores first"]

    D --> D1["schema fields"]
    D --> D2["seeded issue recall"]
    D --> D3["well + volume validity"]
    D --> D4["checkpoint coverage"]
    D --> D5["forbidden pattern hits"]
```

## What Gets Tested

The dataset has 10 tasks across five task types:

```text
protocol_intake        messy request -> structured protocol intent
protocol_review        flawed draft -> findings with code, severity, evidence
worklist_generation    safe plate-map goal -> transfer rows
trajectory_refinement  multi-turn edits -> final artifact and change log
screening_checkpoint   construct/sample mention -> non-operational review gates
```

The signal is practical rather than broad. The harness checks whether the model:

- keeps user constraints intact across turns
- asks for missing source wells, sample identity, labware, volumes, or approvals
- catches seeded defects in draft protocols and plate maps
- emits parseable JSON instead of unstructured prose
- avoids making unsafe or unsupported execution assumptions
- flags screening, provenance, approval, or biosafety-review gates when fixture metadata requires them

## Fixture Boundaries

Included:

```text
colored water transfers
food-dye mixing
mock inventory fields
dummy plate maps
metadata review for construct IDs or unknown samples
```

Excluded:

```text
pathogen instructions
organism engineering procedures
synthesis-ready sequences
culture conditions
clinical handling instructions
instrument-specific execution parameters
```

The public fixture set is meant for engineering signal and regression testing. Passing it does not mean a model is ready for real protocol execution.

## Artifact Contracts

Model responses are expected to contain one top-level JSON object. For a protocol review task, the artifact should look like this:

```json
{
  "findings": [
    {
      "code": "invalid_well_coordinate",
      "severity": "high",
      "evidence": "dest_well B13 is outside a standard 96-well plate",
      "recommendation": "correct the destination map before generating a worklist"
    }
  ],
  "run_readiness": "blocked"
}
```

The scorer then compares returned issue codes against the seeded issues for that task and records missed issues and extra findings.

## Scoring

Scoring is deterministic. Current checks include:

```text
parseable JSON
required fields present
seeded issue recall
false positive count
valid well coordinates
positive and bounded volumes
duplicate destinations
checkpoint recall
forbidden pattern hits
```

Scores are triage values. A low score tells you what to inspect. A high score means the artifact passed these fixtures, not that the model should be trusted with real wetlab execution.

## Install

```bash
python -m pip install -e ".[dev]"
```

For live model runs, set one API key:

```bash
export ANTHROPIC_API_KEY=...
# or
export OPENAI_API_KEY=...
```

## Run

Validate the task file:

```bash
bio-trajectory-eval validate --data data/tasks.jsonl
```

Run a model:

```bash
bio-trajectory-eval run \
  --model claude-sonnet-4-6 \
  --data data/tasks.jsonl \
  --out results/run.jsonl
```

Score a run:

```bash
bio-trajectory-eval score \
  --in results/run.jsonl \
  --data data/tasks.jsonl \
  --out results/run.scored.jsonl
```

Print the report:

```bash
bio-trajectory-eval report --in results/run.scored.jsonl
```

Report output:

```text
protocol signal report
task_type                 count  avg_score  schema_valid
------------------------  -----  ---------  ------------------
protocol_intake               2       91.5  ################.. 90%
protocol_review               2       78.0  ##############.... 75%
worklist_generation           2       96.0  ################## 100%

tasks below 70
task_0004  protocol_review  55.0  missed seeded issue: duplicate_sample_id
```

## Develop

```bash
python -m pytest -q
```

If the package is not installed in the active interpreter:

```bash
PYTHONPATH=src python -m bio_trajectory_eval validate --data data/tasks.jsonl
PYTHONPATH=src python -m pytest -q
```

## Limits

- The fixture set is small.
- Worklist checks currently assume standard plate coordinates.
- The harness does not simulate instruments or validate real protocols.
- Screening checkpoint tasks test metadata handling only.
- Human review is still required for production decisions.
