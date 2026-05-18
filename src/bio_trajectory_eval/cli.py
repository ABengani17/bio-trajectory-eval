from __future__ import annotations

import argparse
import json
from pathlib import Path

from bio_trajectory_eval.checks import scan_package
from bio_trajectory_eval.opentrons import read_opentrons_metadata
from bio_trajectory_eval.schema import AutomationPackage, dump_json, load_package


def cmd_scan(args: argparse.Namespace) -> None:
    package = load_package(args.manifest)
    if args.opentrons_protocol:
        metadata = read_opentrons_metadata(args.opentrons_protocol)
        package = package.model_copy(update={"metadata": metadata, "protocol_file": args.opentrons_protocol})

    result = scan_package(package)
    output = dump_json(result)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)


def cmd_validate(args: argparse.Namespace) -> None:
    package = load_package(args.manifest)
    print(f"validated {package.id}")
    print(f"platform: {package.platform.value}")
    print(f"samples: {len(package.samples)}")
    print(f"transfers: {len(package.transfers)}")


def cmd_report(args: argparse.Namespace) -> None:
    with Path(args.input).open("r", encoding="utf-8") as handle:
        result = json.load(handle)
    summary = result["summary"]
    print(f"package:  {summary['package_id']}")
    print(f"platform: {summary['platform']}")
    print(f"decision: {summary['decision']}")
    print(
        "findings: "
        f"{summary['finding_count']} "
        f"(critical={summary['critical_count']}, high={summary['high_count']}, medium={summary['medium_count']})"
    )
    for item in result["findings"]:
        print()
        print(f"[{item['severity']}] {item['code']}  {item['path']}")
        print(f"  {item['message']}")
        print(f"  {item['recommendation']}")


def cmd_init(args: argparse.Namespace) -> None:
    package = AutomationPackage.model_validate(
        {
            "id": "pkg_demo_001",
            "name": "Demo automation preflight package",
            "platform": "opentrons",
            "metadata": {
                "protocol_name": "Demo dye transfer",
                "author": "Automation team",
                "api_level": "2.16",
                "robot_type": "OT-2",
            },
            "samples": [
                {
                    "id": "dye_blue",
                    "name": "Blue dye",
                    "material_type": "inert",
                    "screening_status": "not_required",
                }
            ],
            "transfers": [
                {
                    "sample_id": "dye_blue",
                    "source_well": "A1",
                    "dest_well": "B1",
                    "volume_ul": 20,
                }
            ],
            "controls": ["blank_water"],
            "approvals": [],
            "decontamination_plan": "",
        }
    )
    output = dump_json(package)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bio-trajectory-eval")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="write a starter automation package manifest")
    init.add_argument("--out")
    init.set_defaults(func=cmd_init)

    validate = subparsers.add_parser("validate", help="validate a package manifest")
    validate.add_argument("--manifest", required=True)
    validate.set_defaults(func=cmd_validate)

    scan = subparsers.add_parser("scan", help="run biosecurity preflight checks")
    scan.add_argument("--manifest", required=True)
    scan.add_argument("--opentrons-protocol", help="optional Opentrons Python protocol to read metadata from")
    scan.add_argument("--out")
    scan.set_defaults(func=cmd_scan)

    report = subparsers.add_parser("report", help="print a human-readable scan report")
    report.add_argument("--in", dest="input", required=True)
    report.set_defaults(func=cmd_report)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
