# Policy and findings

Findings have five fields:

```text
code
severity
path
message
recommendation
```

Current severities:

```text
info
low
medium
high
critical
```

Decision mapping:

```text
critical present      block
high/medium present   review
only low/info/none    pass
```

Policies can override this for specific finding codes with:

```text
record_only
require_review
block_run
```

Important finding codes:

```text
missing_sequence_screening
missing_construct_approval
missing_biosafety_review
missing_bsl_approval
missing_provenance
unknown_material_type
missing_decontamination_plan
missing_controls
undeclared_sample_transfer
invalid_source_well
invalid_destination_well
large_transfer_volume
reused_destination_well
missing_opentrons_api_level
missing_protocol_name
```

Policy-sensitive checks include unknown material handling, sequence-screening requirements, biosafety-review requirements, transfer-volume threshold, high-throughput threshold, and labware geometry.
