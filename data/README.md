# Data

`tasks.jsonl` is the public fixture set. Each line is one validated protocol-signal task.

The fixtures are deliberately non-hazardous:

```text
colored water
food dye
mock buffers
dummy sample IDs
synthetic plate maps
metadata-only construct/sample review fields
```

They exclude:

```text
pathogen instructions
organism engineering procedures
synthesis-ready sequences
culture conditions
clinical sample handling instructions
instrument-specific execution settings
```

Inspect the dataset:

```bash
bio-trajectory-eval validate --data data/tasks.jsonl
```

Task types:

```text
protocol_intake
protocol_review
worklist_generation
trajectory_refinement
screening_checkpoint
```
