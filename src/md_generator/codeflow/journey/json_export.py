"""JSON exporter for journeys, forests, paths, diffs, and analytics.

Converts rich journey objects into stable JSON formats.
"""

from __future__ import annotations

import json
import dataclasses
from enum import Enum
from pathlib import Path
from typing import Any

from md_generator.codeflow.journey.ir import JourneyIR
from md_generator.codeflow.journey.forest import JourneyForest


def _to_json_serializable(obj: Any) -> Any:
    """Helper to recursively convert dataclasses, enums, sets, and paths to JSON-safe primitives."""
    if dataclasses.is_dataclass(obj):
        res = {}
        for f in dataclasses.fields(obj):
            v = getattr(obj, f.name)
            res[f.name] = _to_json_serializable(v)
        return res
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, set):
        return sorted([_to_json_serializable(x) for x in obj])
    elif isinstance(obj, (list, tuple)):
        return [_to_json_serializable(x) for x in obj]
    elif isinstance(obj, dict):
        return {str(k): _to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, Path):
        return str(obj)
    return obj


def journey_ir_to_dict(ir: JourneyIR) -> dict[str, Any]:
    """Convert JourneyIR to a stable, serializable dictionary."""
    return _to_json_serializable(ir)


def journey_forest_to_dict(forest: JourneyForest) -> dict[str, Any]:
    """Convert JourneyForest to a stable, serializable dictionary."""
    return _to_json_serializable(forest)


def write_journey_json(ir: JourneyIR, path: Path) -> None:
    """Write JourneyIR serialization to a JSON file."""
    data = journey_ir_to_dict(ir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_forest_json(forest: JourneyForest, path: Path) -> None:
    """Write JourneyForest serialization to a JSON file."""
    data = journey_forest_to_dict(forest)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_generic_json(obj: Any, path: Path) -> None:
    """Write any arbitrary journey model (diff, path, analysis) to JSON."""
    data = _to_json_serializable(obj)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
