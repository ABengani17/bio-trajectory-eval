# bio-trajectory-eval

This package provides one [labbench](https://pypi.org/project/labbench/) device, `BiosecurityGate`. It checks a run manifest before automation begins and records a JSON audit line. It is a metadata check, not a biosafety decision system.

The scanner reads a JSON automation package (platform, samples, transfers, controls, approvals, decontamination plan) and returns `pass`, `review`, or `block` with coded findings. Optional Opentrons support reads `metadata` / `requirements` from a Python protocol file without executing it.

## What it is not

- Not sequence screening or a screening-provider client
- Not protocol simulation or liquid-handler verification
- Not a substitute for institutional biosafety review

## Install

```bash
python -m pip install -e ".[dev]"
```

## labbench

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

`assert_clearance` raises on `block` (and on `review` when `fail_on_review=True`). Each scan can append one JSON line to `audit_log`.

See `examples/labbench_gate_demo.py`.

## Manifest

Packages are JSON files validated by Pydantic. Main fields:

| Field | Purpose |
| --- | --- |
| `id`, `name`, `platform` | Package identity (`opentrons`, `autoprotocol`, `worklist`, `other`) |
| `metadata` | Protocol name, API level, robot type |
| `samples[]` | Material type, provenance, screening, approvals, biosafety IDs |
| `transfers[]` | Sample ID, wells, volume (µL) |
| `controls`, `approvals`, `decontamination_plan` | Run-support metadata |

Material types include `inert`, `synthetic_dna`, `controlled_construct`, `environmental_sample`, `unknown`, and others (see `schema.py`).

Generate a starter file:

```bash
bio-trajectory-eval init --out my_package.json
```

## Policy

Policies are JSON files (`examples/policy_default.json`, `examples/policy_strict.json`). They set thresholds, material lists, labware geometry, and optional per-finding overrides (`record_only`, `require_review`, `block_run`).

Finding codes and severity rules: [docs/policy.md](docs/policy.md).

## CLI

```bash
bio-trajectory-eval validate --manifest examples/inert_dye_run.json

bio-trajectory-eval scan \
  --manifest examples/construct_screening_hold.json \
  --policy examples/policy_default.json \
  --out results/construct_scan.json

bio-trajectory-eval gate \
  --manifest examples/inert_dye_run.json \
  --policy examples/policy_default.json \
  --audit-log results/gate_audit.jsonl

bio-trajectory-eval report --in results/construct_scan.json
```

Opentrons metadata from a protocol file:

```bash
bio-trajectory-eval scan \
  --manifest examples/inert_dye_run.json \
  --opentrons-protocol examples/opentrons_demo_protocol.py
```

## Example output

`scan` on `examples/construct_screening_hold.json` with the default policy:

```json
{
  "summary": {
    "package_id": "pkg_construct_001",
    "platform": "opentrons",
    "policy_name": "default_biosecurity_gate",
    "decision": "block",
    "finding_count": 3,
    "critical_count": 1,
    "high_count": 1,
    "medium_count": 1
  },
  "findings": [
    {
      "code": "missing_sequence_screening",
      "severity": "critical",
      "path": "samples[0].screening_status",
      "message": "Sample construct_vendor_17 requires a passed screening record.",
      "recommendation": "Attach screening status and record ID before the package can be released."
    }
  ]
}
```

(`report` prints the same fields in plain text.)

## Examples

| File | Expected decision |
| --- | --- |
| `examples/inert_dye_run.json` | pass |
| `examples/environmental_sample_review.json` | review |
| `examples/construct_screening_hold.json` | block |

## Limits

- One default labware rule per package for well validation (96-well plate unless overridden in policy).
- Transfer and throughput checks are policy thresholds, not physics models.
- Map manifest fields to your LIMS, inventory, and approval systems in deployment.

## Develop

```bash
python -m pytest -q
```

Without installing:

```bash
PYTHONPATH=src python -m pytest -q
```
