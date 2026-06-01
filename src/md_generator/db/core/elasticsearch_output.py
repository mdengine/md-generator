"""Elasticsearch-specific output / presentation options."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from md_generator.db.core.elasticsearch_json import DEFAULT_MAX_JSON_BLOCK_CHARS

ALLOWED_MAPPING_MODES = frozenset({"flattened", "summarized", "raw"})
ALLOWED_ANALYZER_FORMATS = frozenset({"chain", "json", "both"})


@dataclass(frozen=True)
class ElasticsearchOutputConfig:
    mapping_mode: str = "flattened"
    include_raw_json: bool = False
    analyzer_format: str = "chain"
    max_json_block_chars: int = DEFAULT_MAX_JSON_BLOCK_CHARS

    def normalized(self) -> ElasticsearchOutputConfig:
        mode = (self.mapping_mode or "flattened").lower().strip()
        if mode not in ALLOWED_MAPPING_MODES:
            mode = "flattened"
        af = (self.analyzer_format or "chain").lower().strip()
        if af not in ALLOWED_ANALYZER_FORMATS:
            af = "chain"
        cap = self.max_json_block_chars
        if cap is None:
            cap = DEFAULT_MAX_JSON_BLOCK_CHARS
        cap = max(0, int(cap))
        return ElasticsearchOutputConfig(
            mapping_mode=mode,
            include_raw_json=bool(self.include_raw_json),
            analyzer_format=af,
            max_json_block_chars=cap,
        )


def elasticsearch_output_from_dict(out: dict[str, Any]) -> ElasticsearchOutputConfig:
    mode = out.get("elasticsearch_mapping_mode") or out.get("mapping_mode") or "flattened"
    raw = out.get("elasticsearch_include_raw_json", out.get("include_raw_json", False))
    af = out.get("elasticsearch_analyzer_format") or out.get("analyzer_format") or "chain"
    cap_raw = out.get("max_json_block_chars", out.get("elasticsearch_max_json_block_chars"))
    cap = DEFAULT_MAX_JSON_BLOCK_CHARS if cap_raw is None else int(cap_raw)
    return ElasticsearchOutputConfig(
        mapping_mode=str(mode),
        include_raw_json=bool(raw),
        analyzer_format=str(af),
        max_json_block_chars=cap,
    ).normalized()
