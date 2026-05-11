from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from bio_trajectory_eval.adapters.anthropic import AnthropicAdapter
from bio_trajectory_eval.adapters.openai import OpenAIAdapter
from bio_trajectory_eval.assessment import assess_outcome
from bio_trajectory_eval.harness import HarnessConfig, run_trajectory
from bio_trajectory_eval.schema import load_trajectories
from bio_trajectory_eval.scoring import TurnLabel, score_trajectory, score_turn_rules


ROOT = Path(__file__).resolve().parents[2]


def load_config(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def build_adapter(model_id: str, timeout_seconds: int):
    lowered = model_id.lower()
    if lowered.startswith("claude"):
        return AnthropicAdapter(model_id, timeout_seconds=timeout_seconds)
    if lowered.startswith(("gpt", "o1", "o3", "o4")):
        return OpenAIAdapter(model_id, timeout_seconds=timeout_seconds)
    raise ValueError(f"Cannot infer adapter for model: {model_id}")


def cmd_run(args: argparse.Namespace) -> None:
    config_data = load_config(Path(args.config))
    model_id = args.model or config_data["model"]
    tier = args.tier or config_data.get("tier")
    harness_config = HarnessConfig(
        max_turns=int(config_data.get("max_turns", 8)),
        timeout_seconds=int(config_data.get("timeout_seconds", 60)),
        retries=int(config_data.get("retries", 2)),
        early_stop_on_refusal=bool(config_data.get("early_stop_on_refusal", True)),
    )
    model = build_adapter(model_id, timeout_seconds=harness_config.timeout_seconds)
    trajectories = load_trajectories(args.data)
    if tier:
        trajectories = [item for item in trajectories if item.difficulty.value == f"tier_{tier}" or item.difficulty.value == tier]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for trajectory in trajectories:
            result = run_trajectory(trajectory, model, harness_config)
            handle.write(json.dumps(result.to_json_dict()) + "\n")


def cmd_score(args: argparse.Namespace) -> None:
    if args.backend != "rules":
        raise ValueError("CLI scoring currently supports --backend rules. Use scoring.score_turn_llm from Python for LLM judge runs.")
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with Path(args.input).open("r", encoding="utf-8") as source, out_path.open("w", encoding="utf-8") as dest:
        for line in source:
            item = json.loads(line)
            labels = []
            for turn in item["turns"]:
                scored = score_turn_rules(turn["user_message"], turn["model_response"])
                turn["handling_label"] = scored.turn_label.value
                turn["scoring_rationale"] = scored.rationale
                labels.append(scored.turn_label)
            trajectory_label = score_trajectory(labels)
            assessment = assess_outcome(item["expected_trajectory_outcome"], labels, trajectory_label)
            item["trajectory_label"] = trajectory_label.value
            item["expectation_met"] = assessment.expectation_met
            item["failure_mode"] = assessment.failure_mode
            item["first_restrictive_turn"] = assessment.first_restrictive_turn
            dest.write(json.dumps(item) + "\n")


def hash_bar(count: int, total: int, width: int = 24) -> str:
    filled = 0 if total == 0 else round((count / total) * width)
    return "#" * filled + "." * (width - filled)


def cmd_report(args: argparse.Namespace) -> None:
    by_tier: dict[str, Counter] = defaultdict(Counter)
    by_failure: dict[str, Counter] = defaultdict(Counter)
    total_by_tier: Counter = Counter()
    with Path(args.input).open("r", encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            by_tier[item["difficulty"]][item["trajectory_label"]] += 1
            by_failure[item["difficulty"]][item.get("failure_mode", "unassessed")] += 1
            total_by_tier[item["difficulty"]] += 1

    print("outcomes")
    print("tier      outcome                 count  share")
    print("--------  ----------------------  -----  ------------------------")
    for tier in sorted(by_tier):
        total = sum(by_tier[tier].values())
        for outcome, count in sorted(by_tier[tier].items()):
            print(f"{tier:<8}  {outcome:<22}  {count:>5}  {hash_bar(count, total)}")
    print()
    print("diagnosis")
    print("tier      failure_mode            count  share")
    print("--------  ----------------------  -----  ------------------------")
    for tier in sorted(by_failure):
        total = total_by_tier[tier]
        for mode, count in sorted(by_failure[tier].items()):
            print(f"{tier:<8}  {mode:<22}  {count:>5}  {hash_bar(count, total)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bio_trajectory_eval")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run")
    run.add_argument("--model")
    run.add_argument("--tier")
    run.add_argument("--out", required=True)
    run.add_argument("--data", default="data/trajectories.jsonl")
    run.add_argument("--config", default="configs/default.toml")
    run.set_defaults(func=cmd_run)

    score = subparsers.add_parser("score")
    score.add_argument("--in", dest="input", required=True)
    score.add_argument("--backend", default="rules")
    score.add_argument("--out", required=True)
    score.set_defaults(func=cmd_score)

    report = subparsers.add_parser("report")
    report.add_argument("--in", dest="input", required=True)
    report.set_defaults(func=cmd_report)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
