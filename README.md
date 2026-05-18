# bio-trajectory-eval

`bio-trajectory-eval` adds a [labbench](https://pypi.org/project/labbench/) device, `BiosecurityGate`, that audits an automation run package before a liquid handler or worklist is scheduled. It reads a JSON manifest, runs policy checks, returns `pass` / `review` / `block`, and can append an audit line.

Sequence screening tools ([commec](https://github.com/ibbis-bio/common-mechanism), IGSC vendor screening, institutional review) answer whether a **sequence or project** is permitted. This package answers whether the **automation job** is documented and consistent: samples declared, screening IDs attached, approvals present, wells valid, cleanup and controls listed. It does not replace biosafety committees or BLAST-based screening.

---

## Who should use this

| Role | Use case |
| --- | --- |
| **Lab automation engineers** | Block robot scheduling when manifest fields are missing; wire gate into labbench Racks |
| **Biosafety / lab ops** | Standardize what must be on a run package before instruments open |
| **LIMS integrators** | Export one JSON package per scheduled run from sample + approval tables |
| **Compliance / security** | Version-controlled policy JSON and append-only scan logs |

---

## Problems this addresses

Automated labs often schedule runs from protocol files alone. That leaves gaps that sequence screeners never see:

| Gap | Risk | How this package helps |
| --- | --- | --- |
| Screening still **pending** but robot queued | Unreleased DNA on deck | `sequence_screening_pending` → review |
| Vendor construct with **no screening record ID** | No audit link to IGSC/commec result | `missing_sequence_screening` → block (default policy) |
| **Environmental / clinical** sample without provenance | Weak chain of custody | `missing_provenance`, `missing_biosafety_review` → review |
| **Unknown** material type in manifest | Unclassified hazard | `unknown_material_type` → review or block (policy) |
| Transfer uses **undeclared** sample ID | Shadow samples on robot | `undeclared_sample_transfer` → review |
| **BSL-2+** without approval ID | Authorization not tied to run | `missing_bsl_approval` → review |
| Large worklist, **empty approvals** | Batch runs without sign-off | `high_throughput_without_approval` → review |
| Biological run, **no decontamination** reference | Cleanup not traceable | `missing_decontamination_plan` → review |

Full finding list and fixes: **[docs/problems_and_solutions.md](docs/problems_and_solutions.md)**.

---

## Where it sits in a screening pipeline

```text
  [Design / order]     [Sequence screening: commec, IGSC vendor, …]
         │                              │
         └──────────┬───────────────────┘
                    ▼
            LIMS + approvals
                    ▼
         automation package.json  ◄── you maintain this
                    ▼
            BiosecurityGate (labbench)
                    ▼
         pass ──► schedule robot
         review ──► human queue
         block ──► do not schedule
```

Integration notes (LIMS mapping, CI, commec handoff): **[docs/integration.md](docs/integration.md)**.

---

## Repository structure

| Path | Purpose |
| --- | --- |
| `src/bio_trajectory_eval/labbench_gate.py` | `BiosecurityGate` labbench device |
| `src/bio_trajectory_eval/checks.py` | Rule checks and decision logic |
| `src/bio_trajectory_eval/schema.py` | Pydantic models for manifest and policy |
| `src/bio_trajectory_eval/opentrons.py` | Read Opentrons `metadata` / `requirements` without executing protocol |
| `src/bio_trajectory_eval/cli.py` | `init`, `validate`, `scan`, `gate`, `report` |
| `examples/` | Sample manifests and policies |
| `docs/policy.md` | Finding codes and severity rules |
| `docs/problems_and_solutions.md` | Problem → fix reference |
| `docs/integration.md` | Pipeline and LIMS integration |

---

## Install

```bash
python -m pip install -e ".[dev]"
```

Requires Python ≥ 3.10 and `labbench` (see `pyproject.toml`).

---

## Quick start

**1. Create a manifest**

```bash
bio-trajectory-eval init --out my_run.json
```

**2. Scan against policy**

```bash
bio-trajectory-eval scan \
  --manifest examples/construct_screening_hold.json \
  --policy examples/policy_default.json \
  --out results/scan.json
```

**3. Read the report**

```bash
bio-trajectory-eval report --in results/scan.json
```

Example `report` output:

```text
package:  pkg_construct_001
platform: opentrons
policy:   default_biosecurity_gate
decision: block
findings: 3 (critical=1, high=1, medium=1)

[critical] missing_sequence_screening  samples[0].screening_status
  Sample construct_vendor_17 requires a passed screening record.
  Attach screening status, screening_record_id, and screening_provider ...
```

---

## labbench usage

```python
import labbench as lb
from bio_trajectory_eval.labbench_gate import BiosecurityGate


class AutomationRack(lb.Rack):
    gate = BiosecurityGate(
        policy_path="examples/policy_default.json",
        audit_log="results/biosecurity_gate_audit.jsonl",
    )

    def preflight(self, manifest: str):
        return self.gate.assert_clearance(manifest)


with AutomationRack() as rack:
    rack.preflight("examples/inert_dye_run.json")
```

- `assert_clearance` raises on `block` (and on `review` if `fail_on_review=True`).
- `scan` returns findings without raising.
- `audit_log` receives one JSON object per scan (full `ScanResult`).

Runnable demo: `examples/labbench_gate_demo.py`.

---

## Automation package (manifest)

JSON file validated by Pydantic. One file per scheduled automation run.

### Package-level fields

| Field | Required | Purpose |
| --- | --- | --- |
| `id`, `name` | yes | Stable run package ID and display name |
| `platform` | yes | `opentrons`, `autoprotocol`, `worklist`, `other` |
| `requester`, `project_id` | no | Who ordered the run; map from LIMS project |
| `metadata` | no | Protocol name, API level, robot type |
| `samples` | no* | Material declarations (*required if transfers reference them) |
| `transfers` | no | Well-level liquid movements (µL) |
| `controls` | no | Blank / negative / process controls (required for biological materials under default policy) |
| `approvals` | no | Run or batch sign-off IDs |
| `decontamination_plan` | no | SOP reference or text for deck cleanup |
| `notes` | no | Free text for reviewers |

### Per-sample fields

| Field | Purpose |
| --- | --- |
| `material_type` | `inert`, `synthetic_dna`, `controlled_construct`, `environmental_sample`, `unknown`, … |
| `provenance_id` | LIMS accession, intake form, vendor order |
| `screening_status` | `not_required`, `passed`, `pending`, `missing` |
| `screening_record_id` | Link to commec output, IGSC vendor screening ID, internal ticket |
| `screening_provider` | Which system produced the record (`commec`, vendor name, …) |
| `approval_id` | Construct or BSL approval reference |
| `biosafety_review_id` | Institutional biosafety ticket |
| `biosafety_level` | 1–4 |
| `external` | Sample from outside the lab (triggers provenance checks) |

### Material types and default policy

| `material_type` | Default checks |
| --- | --- |
| `inert`, `buffer`, `reagent` | Geometry / transfer consistency |
| `synthetic_dna`, `controlled_construct` | Screening passed + record ID + approval |
| `organism`, `cell_line`, `clinical_sample`, `environmental_sample` | Biosafety review + provenance (if external) + controls + decontamination |
| `unknown` | Classify or block/review per policy |

---

## Policy

Policies are JSON (`examples/policy_default.json`, `examples/policy_strict.json`).

| Knob | Effect |
| --- | --- |
| `require_sequence_screening_for` | Material types that need `screening_status: passed` and `screening_record_id` |
| `block_on_missing_sequence_screening` | Missing/failed screening → `critical` (block) vs `high` (review) |
| `require_biosafety_review_for` | Material types that need `biosafety_review_id` |
| `block_on_unknown_material` | `unknown` → block instead of review |
| `max_transfer_ul_without_review` | Volume threshold per transfer |
| `high_throughput_transfer_count` | Transfer count requiring `approvals` |
| `default_labware` | Row/column bounds for well validation |
| `finding_actions` | Per-code override: `record_only`, `require_review`, `block_run` |

Details: **[docs/policy.md](docs/policy.md)**.

---

## CLI

| Command | Description |
| --- | --- |
| `init` | Write a starter manifest |
| `validate` | Parse manifest only |
| `scan` | Run checks; optional `--opentrons-protocol` to merge metadata |
| `gate` | Run `BiosecurityGate.assert_clearance` |
| `report` | Print human-readable results from scan JSON |

```bash
bio-trajectory-eval validate --manifest examples/inert_dye_run.json

bio-trajectory-eval scan \
  --manifest examples/inert_dye_run.json \
  --opentrons-protocol examples/opentrons_demo_protocol.py

bio-trajectory-eval gate \
  --manifest examples/inert_dye_run.json \
  --policy examples/policy_default.json \
  --audit-log results/gate_audit.jsonl
```

---

## Examples

| Manifest | Expected | Illustrates |
| --- | --- | --- |
| `examples/inert_dye_run.json` | pass | Inert dye demo; complete metadata |
| `examples/environmental_sample_review.json` | review | Missing provenance, biosafety, controls, cleanup |
| `examples/construct_screening_hold.json` | block | Missing screening + approval; invalid well |

Policies: `examples/policy_default.json`, `examples/policy_strict.json`.

---

## What this is not

- Not a nucleotide sequence screener (use commec, IGSC providers, or institutional tools)
- Not Opentrons motion verification or deck layout simulation
- Not a replacement for IBC / biosafety sign-off — it checks that sign-off **IDs are present** on the package

---

## Limits

- One `default_labware` rule per scan (96-well by default); per-plate rules are policy-level, not per-transfer yet.
- Opentrons import reads static `metadata` / `requirements` only.
- Manifest must be produced by your LIMS/export pipeline; this repo does not ship LIMS connectors.

---

## Develop

```bash
python -m pytest -q
```

```bash
PYTHONPATH=src python -m pytest -q
```
