# Integration

## Recommended pipeline

```text
Design / order ──► sequence screening (commec, IGSC vendor, internal)
       │
       ▼
LIMS + approvals ──► automation package manifest (JSON)
       │
       ▼
BiosecurityGate.scan / assert_clearance  ──► pass | review | block
       │
       ├── pass ──► schedule Opentrons / worklist / Autoprotocol
       ├── review ──► biosafety or lab ops queue
       └── block ──► fix manifest, do not schedule
```

## labbench Rack

`BiosecurityGate` is a [labbench](https://pypi.org/project/labbench/) `Device`. Call it in the same Rack as the liquid handler so preflight and instrument open share logging context.

```python
import labbench as lb
from bio_trajectory_eval.labbench_gate import BiosecurityGate

class AutomationRack(lb.Rack):
    gate = BiosecurityGate(
        policy_path="examples/policy_default.json",
        audit_log="results/biosecurity_gate_audit.jsonl",
        fail_on_review=False,  # set True to treat review like block
    )

    def run(self, manifest: str):
        self.gate.assert_clearance(manifest)
        # open liquid handler here
```

See `examples/labbench_gate_demo.py`.

## Linking screening results

After an external screening step, copy these fields onto each affected `samples[]` row:

| Field | Example value |
| --- | --- |
| `screening_status` | `passed`, `pending`, `missing` |
| `screening_record_id` | Vendor order screening ID, commec JSON path, LIMS ticket |
| `screening_provider` | `igsc_vendor_acme`, `commec`, `internal_bioscreen` |

commec writes `.screen.json` per sequence; your exporter should map that file path or a hash into `screening_record_id`.

## LIMS and metadata standards

Map manifest fields from systems you already use:

| Manifest field | Typical LIMS / form source |
| --- | --- |
| `provenance_id` | Sample accession, intake ID |
| `approval_id` | Order review, IBC protocol number |
| `biosafety_review_id` | Biosafety ticket, risk assessment ID |
| `project_id`, `requester` | Project code, PI netid |
| `controls` | Study design control list |
| `decontamination_plan` | SOP document ID or URL |

[Biodesign Metadata Exchange (BMDE)](https://github.com/Lattice-Automation/Biodesign-Metadata-Exchange) targets design-time provenance for synthesis orders. This manifest targets run-time automation packages. You can populate both from the same LIMS export step.

## CI and repositories

Scan manifests in CI before merging protocol changes:

```bash
bio-trajectory-eval scan --manifest packages/run_042.json --policy policies/production.json --out results/run_042_scan.json
test "$(jq -r .summary.decision results/run_042_scan.json)" = "pass"
```

Keep policy JSON in version control per site or per instrument room.

## Audit log

With `audit_log` set, each scan appends one JSON line containing the full `ScanResult`. Append-only logs support post-incident review without replacing LIMS records.
