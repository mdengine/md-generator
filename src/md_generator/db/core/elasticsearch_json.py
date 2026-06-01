"""JSON fence blocks for Elasticsearch markdown exports."""

from __future__ import annotations

import json
from typing import Any

DEFAULT_MAX_JSON_BLOCK_CHARS = 32_000


def effective_json_block_limit(max_chars: int | None) -> int:
    """Return ``0`` for unlimited; otherwise a positive cap."""
    if max_chars is None:
        return DEFAULT_MAX_JSON_BLOCK_CHARS
    return max(0, int(max_chars))


def json_block(
    obj: Any,
    *,
    max_chars: int | None = None,
    warnings: list[str] | None = None,
    label: str = "JSON",
) -> str:
    """Render a fenced JSON block, optionally truncating and recording a warning."""
    text = json.dumps(obj, sort_keys=True, indent=2)
    limit = effective_json_block_limit(max_chars)
    if limit > 0 and len(text) > limit:
        omitted = len(text) - limit
        text = text[:limit] + f"\n… ({omitted:,} chars omitted)"
        if warnings is not None:
            warnings.append(f"{label} truncated ({limit:,} char cap)")
    return f"```json\n{text}\n```\n\n"
