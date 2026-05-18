from __future__ import annotations

import ast
from pathlib import Path

from bio_trajectory_eval.schema import ProtocolMetadata


def _literal_dict(tree: ast.Module, name: str) -> dict:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    try:
                        value = ast.literal_eval(node.value)
                    except Exception:
                        return {}
                    return value if isinstance(value, dict) else {}
    return {}


def read_opentrons_metadata(path: str | Path) -> ProtocolMetadata:
    text = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(text)
    metadata = _literal_dict(tree, "metadata")
    requirements = _literal_dict(tree, "requirements")
    return ProtocolMetadata(
        protocol_name=str(metadata.get("protocolName", metadata.get("protocol_name", ""))),
        author=str(metadata.get("author", "")),
        api_level=str(requirements.get("apiLevel", metadata.get("apiLevel", ""))),
        robot_type=str(requirements.get("robotType", "")),
    )
