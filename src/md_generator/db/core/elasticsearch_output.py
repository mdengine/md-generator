"""Elasticsearch-specific output / presentation options."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ALLOWED_MAPPING_MODES = frozenset({"flattened", "summarized", "raw"})
ALLOWED_ANALYZER_FORMATS = frozenset({"chain", "json", "both"})


@dataclass(frozen=True)
class ElasticsearchOutputConfig:
    mapping_mode: str = "flattened"
    include_raw_json: bool = False
    analyzer_format: str = "chain"

    def normalized(self) -> ElasticsearchOutputConfig:
        mode = (self.mapping_mode or "flattened").lower().strip()
        if mode not in ALLOWED_MAPPING_MODES:
            mode = "flattened"
        af = (self.analyzer_format or "chain").lower().strip()
        if af not in ALLOWED_ANALYZER_FORMATS:
            af = "chain"
        if self.include_raw_json and mode != "raw":
            pass  # raw JSON blocks added alongside flattened when include_raw_json
        return ElasticsearchOutputConfig(
            mapping_mode=mode,
            include_raw_json=bool(self.include_raw_json),
            analyzer_format=af,
        )


def elasticsearch_output_from_dict(out: dict[str, Any]) -> ElasticsearchOutputConfig:
    mode = out.get("elasticsearch_mapping_mode") or out.get("mapping_mode") or "flattened"
    raw = out.get("elasticsearch_include_raw_json", out.get("include_raw_json", False))
    af = out.get("elasticsearch_analyzer_format") or out.get("analyzer_format") or "chain"
    return ElasticsearchOutputConfig(
        mapping_mode=str(mode),
        include_raw_json=bool(raw),
        analyzer_format=str(af),
    ).normalized()
