from __future__ import annotations

from md_generator.db.core.elasticsearch_json import json_block
from md_generator.db.core.elasticsearch_warnings import (
    ExportWarningCollector,
    finalize_markdown_with_warnings,
    format_export_warnings_section,
)


def test_json_block_unlimited_when_zero() -> None:
    big = {"data": "x" * 50_000}
    block = json_block(big, max_chars=0)
    assert "chars omitted" not in block
    assert "x" * 100 in block


def test_json_block_truncates_and_records_warning() -> None:
    big = {"key": "a" * 10_000}
    warnings: list[str] = []
    block = json_block(big, max_chars=500, warnings=warnings, label="Mappings")
    assert "chars omitted" in block
    assert len(warnings) == 1
    assert "Mappings truncated" in warnings[0]


def test_export_warning_collector_manifest() -> None:
    c = ExportWarningCollector()
    c.add("json_truncated", "Mappings truncated (500 char cap)", file="elasticsearch/indices/x.md")
    manifest = c.to_manifest_list()
    assert manifest[0]["code"] == "json_truncated"
    assert manifest[0]["file"] == "elasticsearch/indices/x.md"


def test_finalize_markdown_with_warnings_appends_section() -> None:
    body = finalize_markdown_with_warnings("# Title\n\nBody.\n", ["JSON truncated"])
    assert "## Export Warnings" in body
    assert "- JSON truncated" in body
    assert format_export_warnings_section([]) == ""
