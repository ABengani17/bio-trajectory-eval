# Problems and solutions

This table is the operational reference for findings. Each row ties a lab automation failure mode to manifest fields, a finding code, and the usual fix.

| Problem | Typical cause | Manifest fields | Finding code | What to do |
| --- | --- | --- | --- | --- |
| Robot run scheduled before screening completes | Vendor order still in queue | `samples[].screening_status`, `screening_record_id` | `sequence_screening_pending` | Hold scheduling until status is `passed` and record ID is set |
| Synthetic DNA on deck without screening proof | Manifest copied from worklist only | `screening_status`, `screening_record_id`, `screening_provider` | `missing_sequence_screening` | Link IGSC provider result, internal commec run, or LIMS screening ticket |
| Construct lacks internal sign-off | Only vendor COA attached | `approval_id` | `missing_construct_approval` | Add PI, biosafety, or order-review ID from your approval system |
| Environmental sample with no chain of custody | Collaborator tube label only | `provenance_id`, `external` | `missing_provenance` | Export LIMS sample ID or intake form reference |
| Unknown material in automation package | Placeholder type left default | `material_type` | `unknown_material_type` | Classify material; strict policy blocks, default policy reviews |
| BSL-2+ material without authorization | BSL field set but no approval row | `biosafety_level`, `approval_id` | `missing_bsl_approval` | Attach approved protocol or IBC registration number |
| Clinical / cell / organism work without biosafety ticket | New workflow, old manifest template | `biosafety_review_id` | `missing_biosafety_review` | Route to institutional biosafety; add review ID to manifest |
| Transfer references sample not in manifest | Protocol edited after manifest export | `transfers[].sample_id`, `samples[]` | `undeclared_sample_transfer` | Add sample row or remove orphan transfer |
| Wells off plate map | Wrong labware or 384 vs 96 confusion | `transfers[]`, policy `default_labware` | `invalid_source_well`, `invalid_destination_well` | Fix coordinates or set labware rule in policy |
| High-throughput batch without batch approval | Large worklist, empty `approvals` | `transfers`, `approvals` | `high_throughput_without_approval` | Add batch reviewer sign-off for N+ transfers (threshold in policy) |
| Biological package with no cleanup plan | Assumed “standard SOP” | `decontamination_plan` | `missing_decontamination_plan` | Paste or reference deck cleanup / waste SOP ID |
| Biological package with no controls declared | Only unknowns listed | `controls` | `missing_controls` | List blank, negative, or process controls used in the run |
| Opentrons package missing traceability | Metadata not merged from `.py` | `metadata.protocol_name`, `metadata.api_level` | `missing_protocol_name`, `missing_opentrons_api_level` | Run `scan --opentrons-protocol` or fill metadata in manifest |

## Decisions

| Decision | Meaning for scheduling |
| --- | --- |
| `pass` | No medium+ findings under policy; automation may proceed |
| `review` | Human must clear findings before instruments open |
| `block` | Do not schedule; fix manifest or escalate |

Policy can promote a finding to `block` via `finding_actions` (see [policy.md](policy.md)).

## Sequence screening vs this package

| Layer | Tool examples | Question answered |
| --- | --- | --- |
| Sequence | [commec](https://github.com/ibbis-bio/common-mechanism), IGSC vendor screening, SecureDNA | Is this nucleotide sequence regulated or high risk? |
| Run package (this repo) | `bio-trajectory-eval` | Is the automation job documented and internally consistent before the robot runs? |
| Institutional | IBC, biosafety office | Is the work permitted in this space at this BSL? |

This package expects screening outcomes to appear in the manifest (`screening_status`, `screening_record_id`, `screening_provider`). It does not run BLAST or HMM searches.
