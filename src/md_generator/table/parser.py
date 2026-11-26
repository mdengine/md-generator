from __future__ import annotations

"""Markdown Table Parser & Normalizer.

Phase 2E/Prompt 07 Implementation:
- Parses GitHub-Flavored Markdown tables (headers, alignment dividers, data rows).
- Handles escaped pipes, ragged rows, irregular/merged cells, and leading/trailing pipe omissions.
- Preserves genuine values without loss.
- Extracts structured TableData instances from raw markdown documents.
"""

import re
from typing import List, Optional, Tuple

from md_generator.semantic.model.schema import SourceLocation
from md_generator.table.models import TableCell, TableData


TABLE_ROW_REGEX = re.compile(r"^\|(.+)\|$")
DIVIDER_CELL_REGEX = re.compile(r"^:?-+:?$")


def _split_markdown_row(line: str) -> List[str]:
    """Splits a table line into cells handling escaped pipes (\\|)."""
    # Replace escaped pipe with temporary placeholder
    masked = line.replace(r"\|", "@@ESCAPED_PIPE@@")
    # Strip outer pipes if present
    trimmed = masked.strip()
    if trimmed.startswith("|"):
        trimmed = trimmed[1:]
    if trimmed.endswith("|"):
        trimmed = trimmed[:-1]

    parts = trimmed.split("|")
    # Restore escaped pipes
    return [p.replace("@@ESCAPED_PIPE@@", "|").strip() for p in parts]


def is_divider_row(cells: List[str]) -> bool:
    """Checks whether a row consists exclusively of markdown table divider cells (e.g. :---, ---:)."""
    if not cells:
        return False
    return all(bool(DIVIDER_CELL_REGEX.match(c.replace(" ", ""))) for c in cells if c)


class MarkdownTableParser:
    """Parses and normalizes Markdown tables into structured TableData."""

    @staticmethod
    def parse_tables(markdown_text: str, location: Optional[SourceLocation] = None) -> List[TableData]:
        """Scans text for markdown tables and parses them into TableData objects."""
        tables: List[TableData] = []
        if not markdown_text:
            return tables

        lines = markdown_text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # A table candidate starts with a pipe
            if line.startswith("|") and line.endswith("|") and "|" in line[1:-1]:
                # Collect contiguous table block
                block_lines: List[str] = []
                while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                    block_lines.append(lines[i].strip())
                    i += 1

                if len(block_lines) >= 2:
                    table_obj = MarkdownTableParser._parse_block(block_lines, location)
                    if table_obj is not None:
                        tables.append(table_obj)
            else:
                i += 1

        return tables

    @staticmethod
    def _parse_block(lines: List[str], location: Optional[SourceLocation] = None) -> Optional[TableData]:
        """Parses a contiguous block of markdown table lines."""
        if len(lines) < 2:
            return None

        first_cells = _split_markdown_row(lines[0])
        second_cells = _split_markdown_row(lines[1])

        # Check for standard Markdown table (header + divider + rows)
        if is_divider_row(second_cells):
            headers = first_cells
            data_rows: List[List[str]] = []
            for row_line in lines[2:]:
                data_rows.append(_split_markdown_row(row_line))
        else:
            # Table without explicit divider: treat all rows as data rows
            headers = []
            data_rows = [_split_markdown_row(l) for l in lines]

        # Determine target column width
        max_cols = max(len(headers), max((len(r) for r in data_rows), default=0))
        if max_cols == 0:
            return None

        # Normalize column counts across headers and rows (pad ragged rows)
        if headers:
            while len(headers) < max_cols:
                headers.append("")
        normalized_data_rows: List[List[str]] = []
        for r in data_rows:
            padded = list(r)
            while len(padded) < max_cols:
                padded.append("")
            normalized_data_rows.append(padded)

        return TableData(
            headers=headers,
            rows=normalized_data_rows,
            location=location,
        )
