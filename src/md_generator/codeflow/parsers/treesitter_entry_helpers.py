"""Shared helpers for framework entry detection in Tree-sitter parsers."""

from __future__ import annotations

from md_generator.codeflow.models.ir import EntryKind, EntryRecord, FileParseResult


def append_entry(
    fr: FileParseResult,
    *,
    seen: set[str],
    symbol_id: str,
    label: str,
    file_path: str,
    line: int,
    kind: EntryKind = EntryKind.API_REST,
) -> None:
    if symbol_id in seen:
        return
    seen.add(symbol_id)
    fr.entries.append(
        EntryRecord(
            symbol_id=symbol_id,
            kind=kind,
            label=label,
            file_path=file_path,
            line=line,
        ),
    )
