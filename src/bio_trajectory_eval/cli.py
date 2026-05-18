from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from bio_trajectory_eval.harness import HarnessConfig, run_task
from bio_trajectory_eval.schema import load_tasks
from bio_trajectory_eval.scoring import parse_json_artifact, score_artifact


def load_config(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def build_adapter(model_id: str, timeout_seconds: int):
    lowered = model_id.lower()
    if lowered.startswith("claude"):
        from bio_trajectory_eval.adapters.anthropic import AnthropicAdapter

        return AnthropicAdapter(model_id, timeout_seconds=timeout_seconds)
    if lowered.startswith(("gpt", "o1", "o3", "o4")):
        from bio_trajectory_eval.adapters.openai import OpenAIAdapter

        return OpenAIAdapter(model_id, timeout_seconds=timeout_seconds)
    raise ValueError(f"Cannot infer adapter for model: {model_id}")


def cmd_validate(args: argparse.Namespace) -> None:
    tasks = load_tasks(args.data)
    counts = Counter(task.task_type.value for task in tasks)
    print(f"validated {len(tasks)} tasks")
    for task_type, count in sorted(counts.items()):
        print(f"{task_type}: {count}")


def cmd_run(args: argparse.Namespace) -> None:
    config_data = load_config(Path(args.config))
    model_id = args.model or config_data.get("model")
    if not model_id:
        raise ValueError("provide --model or set model in config")
    config = HarnessConfig(
        timeout_seconds=int(config_data.get("timeout_seconds", 60)),
        retries=int(config_data.get("retries", 2)),
    )
    tasks = load_tasks(args.data)
    if args.type:
        tasks = [task for task in tasks if task.task_type.value == args.type]

    model = build_adapter(model_id, timeout_seconds=config.timeout_seconds)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for task in tasks:
            result = run_task(task, model, config)
            handle.write(json.dumps(result.to_json_dict()) + "\n")


def cmd_score(args: argparse.Namespace) -> None:
    tasks = {task.id: task for task in load_tasks(args.data)}
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with Path(args.input).open("r", encoding="utf-8") as source, out_path.open("w", encoding="utf-8") as dest:
        for line in source:
            row = json.loads(line)
            task = tasks[row["task_id"]]
            artifact = row.get("artifact")
            parse_error = row.get("parse_error")
            if artifact is None and row.get("response_text"):
                artifact, parse_error = parse_json_artifact(row["response_text"])
            scored = score_artifact(task, artifact, row.get("response_text", ""))
            row.update(
                {
                    "artifact": artifact,
                    "parse_error": parse_error,
                    "score": scored.score,
                    "schema_valid": scored.schema_valid,
                    "metrics": scored.metrics,
                    "findings": scored.findings,
                }
            )
            dest.write(json.dumps(row) + "\n")


def _bar(value: float, width: int = 18) -> str:
    filled = round(value * width)
    return "#" * filled + "." * (width - filled)


def cmd_report(args: argparse.Namespace) -> None:
    by_type: dict[str, list[dict]] = defaultdict(list)
    with Path(args.input).open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            by_type[row["task_type"]].append(row)

    print("protocol signal report")
    print("task_type                 count  avg_score  schema_valid")
    print("------------------------  -----  ---------  ------------------")
    for task_type in sorted(by_type):
        rows = by_type[task_type]
        avg_score = sum(float(row.get("score", 0)) for row in rows) / len(rows)
        valid_rate = sum(1 for row in rows if row.get("schema_valid")) / len(rows)
        print(f"{task_type:<24}  {len(rows):>5}  {avg_score:>9.1f}  {_bar(valid_rate)} {valid_rate:.0%}")

    failing = sorted(
        [row for rows in by_type.values() for row in rows if float(row.get("score", 0)) < args.fail_below],
        key=lambda row: float(row.get("score", 0)),
    )
    if failing:
        print()
        print(f"tasks below {args.fail_below:g}")
        for row in failing[: args.limit]:
            reason = "; ".join(row.get("findings", [])[:2]) or row.get("parse_error") or "low score"
            print(f"{row['task_id']}  {row['task_type']}  {row.get('score', 0):.1f}  {reason}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bio-trajectory-eval")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--data", default="data/tasks.jsonl")
    validate.set_defaults(func=cmd_validate)

    run = subparsers.add_parser("run")
    run.add_argument("--model")
    run.add_argument("--type")
    run.add_argument("--out", required=True)
    run.add_argument("--data", default="data/tasks.jsonl")
    run.add_argument("--config", default="configs/default.toml")
    run.set_defaults(func=cmd_run)

    score = subparsers.add_parser("score")
    score.add_argument("--in", dest="input", required=True)
    score.add_argument("--out", required=True)
    score.add_argument("--data", default="data/tasks.jsonl")
    score.set_defaults(func=cmd_score)

    report = subparsers.add_parser("report")
    report.add_argument("--in", dest="input", required=True)
    report.add_argument("--fail-below", type=float, default=70)
    report.add_argument("--limit", type=int, default=10)
    report.set_defaults(func=cmd_report)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
