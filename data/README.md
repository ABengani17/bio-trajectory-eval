# Data

The scanner reads a package manifest: a JSON file that describes the automation platform, protocol metadata, samples, transfers, controls, approvals, and decontamination plan.

The current examples live in `examples/`:

```text
pass_inert_opentrons.json
review_environmental_samples.json
block_construct_missing_screening.json
opentrons_demo_protocol.py
```

Run:

```bash
bio-trajectory-eval scan --manifest examples/block_construct_missing_screening.json
```
