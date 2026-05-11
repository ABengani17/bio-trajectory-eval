# bio-trajectory-eval

`bio-trajectory-eval` tests whether AI-bio safeguards hold across multi-turn trajectories. Most public bio-risk evals score isolated prompts. This repo uses safe proxy domains to test whether a model can answer each turn in a way that looks acceptable while still giving concerning cumulative assistance across a sequence.

## The question we're trying to answer

Do frontier model safeguards behave differently when benign-looking biology questions are evaluated as trajectories rather than isolated turns?

## Repo layout

```text
bio-trajectory-eval/
├── README.md
├── pyproject.toml
├── .gitignore
├── configs/
│   └── default.toml
├── data/
│   ├── trajectories.jsonl
│   ├── proxy_domains.md
│   └── README.md
├── src/bio_trajectory_eval/
│   ├── __init__.py
│   ├── schema.py
│   ├── harness.py
│   ├── scoring.py
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── anthropic.py
│   │   └── openai.py
│   └── cli.py
├── notebooks/
│   └── walkthrough.ipynb
├── tests/
│   ├── test_schema.py
│   ├── test_scoring.py
│   └── test_harness.py
├── docs/
│   ├── methodology.md
│   ├── proxy_rationale.md
│   ├── scoring_rubric.md
│   └── future_work.md
└── results/
    └── .gitkeep
```

## How to run it

```bash
python -m bio_trajectory_eval run --model claude-sonnet-4-6 --tier 2 --out results/run_2026_05_11.jsonl
python -m bio_trajectory_eval score --in results/run_2026_05_11.jsonl --backend rules --out results/run_2026_05_11.scored.jsonl
python -m bio_trajectory_eval report --in results/run_2026_05_11.scored.jsonl
```

The Anthropic adapter reads `ANTHROPIC_API_KEY`. The OpenAI adapter reads `OPENAI_API_KEY`. API keys are never written to result files.

## Sample output

Illustrative only. This block is not a reported model result.

```text
tier      outcome                 count  share
--------  ----------------------  -----  ------------------------
tier_2    compliant_throughout        3  ########................
tier_2    redirected                  6  ################........
```

## What's intentionally out of scope

- Single-turn evals, which are already covered by work such as WMDP.
- Dangerous-adjacent content, which belongs in a gated workstream.
- Cross-modal bio uplift testing.
- Claims about model safety from proxy results alone.

## Connection to existing work

This repo complements WMDP, Defenses in Depth project 2, SecureBio's detection work as a sister workstream, and the gene synthesis screening literature. It isolates one missing method: trajectory-level testing with public, safe proxy items.

## Future work

See [docs/future_work.md](docs/future_work.md).
