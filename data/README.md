# Data

`trajectories.jsonl` is the public proxy dataset. Each line is one validated trajectory.

The current file has 27 items:

```text
tier_1   8  benign controls
tier_2  10  safe proxies that mirror dual-use workflow shapes
tier_3   9  safe proxies that should trigger early redirection
```

Each trajectory has user turns, expected handling labels, a trajectory-level concern, and notes on the proxy mapping. The expected labels are not model outputs. They are the reviewer-authored target behavior used to interpret a run.

The items use safe proxy domains only. They do not contain organism engineering instructions, operational protocol details, sequences, dose information, delivery instructions, or hazardous-agent content.

To inspect the dataset:

```bash
PYTHONPATH=src python - <<'PY'
from collections import Counter
from bio_trajectory_eval.schema import load_trajectories

items = load_trajectories("data/trajectories.jsonl")
print(len(items))
print(Counter(item.difficulty.value for item in items))
print(Counter(item.proxy_domain.value for item in items))
PY
```
