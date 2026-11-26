from __future__ import annotations

"""Structural Table Intelligence Models & Schema.

Phase 2E/Prompt 07 Implementation:
- TableCell: fine-grained cell representation with row/col spans, header indicator,
  and authentic coordinates (only when supplied by extraction backend; never fabricated).
- TableData: structured table schema supporting headers, rows, cell grid, caption,
  source location, deterministic hash-based table ID, and markdown/CSV/JSON serialization.
"""

from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from md_generator.semantic.model.schema import SourceLocation


@dataclass
class TableCell:
    """Represents a single table cell with structural and geometric metadata."""
    content: str
    row_index: int
    col_index: int
    row_span: int = 1
    col_span: int = 1
    is_header: bool = False
    # Authentic bounding box coordinates: e.g. {"x0": float, "y0": float, "x1": float, "y1": float}
    # ONLY populated when extraction backend (e.g. PDF table extractor) provides real coordinates.
    # NEVER fabricated from markdown text offsets.
    coordinates: Optional[Dict[str, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "row_index": self.row_index,
            "col_index": self.col_index,
            "row_span": self.row_span,
            "col_span": self.col_span,
            "is_header": self.is_header,
            "coordinates": self.coordinates,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TableCell:
        return cls(
            content=data.get("content", ""),
            row_index=data.get("row_index", 0),
            col_index=data.get("col_index", 0),
            row_span=data.get("row_span", 1),
            col_span=data.get("col_span", 1),
            is_header=data.get("is_header", False),
            coordinates=data.get("coordinates"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TableData:
    """Structured representation of a document table."""
    headers: List[str]
    rows: List[List[str]]
    cells: List[TableCell] = field(default_factory=list)
    caption: Optional[str] = None
    location: Optional[SourceLocation] = None
    table_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.table_id:
            # Generate deterministic canonical table ID from headers + rows content
            raw_repr = json.dumps({"h": self.headers, "r": self.rows}, sort_keys=True)
            self.table_id = f"tbl_{hashlib.sha256(raw_repr.encode('utf-8')).hexdigest()[:16]}"

        # If cells were not explicitly provided, build from headers and rows
        if not self.cells and (self.headers or self.rows):
            self._build_cells()

    def _build_cells(self) -> None:
        cells: List[TableCell] = []
        if self.headers:
            for c_idx, h in enumerate(self.headers):
                cells.append(
                    TableCell(
                        content=h,
                        row_index=0,
                        col_index=c_idx,
                        is_header=True,
                    )
                )
        for r_idx, row in enumerate(self.rows):
            actual_row = r_idx + (1 if self.headers else 0)
            for c_idx, val in enumerate(row):
                cells.append(
                    TableCell(
                        content=val,
                        row_index=actual_row,
                        col_index=c_idx,
                        is_header=False,
                    )
                )
        self.cells = cells

    @property
    def num_rows(self) -> int:
        return len(self.rows) + (1 if self.headers else 0)

    @property
    def num_cols(self) -> int:
        if self.headers:
            return len(self.headers)
        if self.rows:
            return max((len(r) for r in self.rows), default=0)
        return 0

    def get_cell(self, row: int, col: int) -> Optional[TableCell]:
        for c in self.cells:
            if c.row_index == row and c.col_index == col:
                return c
        return None

    def get_column_values(self, col_index: int) -> List[str]:
        values = []
        for row in self.rows:
            if 0 <= col_index < len(row):
                values.append(row[col_index])
            else:
                values.append("")
        return values

    def to_markdown(self) -> str:
        """Formats the table as a clean GitHub-flavored markdown table with aligned columns."""
        if not self.headers and not self.rows:
            return ""

        # Determine column count
        col_count = self.num_cols
        if col_count == 0:
            return ""

        # Normalize headers
        effective_headers = list(self.headers) if self.headers else [f"Col {i+1}" for i in range(col_count)]
        while len(effective_headers) < col_count:
            effective_headers.append("")

        # Normalize rows
        normalized_rows: List[List[str]] = []
        for r in self.rows:
            padded = list(r)
            while len(padded) < col_count:
                padded.append("")
            # Clean inner newlines and unescaped pipes
            clean_cells = [c.replace("\n", " ").replace("|", "\\|").strip() for c in padded]
            normalized_rows.append(clean_cells)

        # Compute max width per column
        col_widths = [len(h) for h in effective_headers]
        for r in normalized_rows:
            for c_idx, val in enumerate(r):
                col_widths[c_idx] = max(col_widths[c_idx], len(val))
        col_widths = [max(w, 3) for w in col_widths]  # Min 3 dashes

        # Format Header
        header_cells = [h.ljust(col_widths[i]) for i, h in enumerate(effective_headers)]
        header_line = "| " + " | ".join(header_cells) + " |"

        # Format Divider
        divider_cells = ["-" * col_widths[i] for i in range(col_count)]
        divider_line = "| " + " | ".join(divider_cells) + " |"

        lines = [header_line, divider_line]

        # Format Data Rows
        for r in normalized_rows:
            row_cells = [r[i].ljust(col_widths[i]) for i in range(col_count)]
            lines.append("| " + " | ".join(row_cells) + " |")

        md_str = "\n".join(lines)
        if self.caption:
            md_str = f"**Table: {self.caption}**\n\n{md_str}"
        return md_str

    def to_csv(self) -> str:
        """Formats table as CSV."""
        import csv
        import io
        buf = io.StringIO()
        writer = csv.writer(buf)
        if self.headers:
            writer.writerow(self.headers)
        for r in self.rows:
            writer.writerow(r)
        return buf.getvalue()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_id": self.table_id,
            "headers": self.headers,
            "rows": self.rows,
            "num_rows": self.num_rows,
            "num_cols": self.num_cols,
            "caption": self.caption,
            "location": self.location.to_dict() if self.location and hasattr(self.location, "to_dict") else None,
            "cells": [c.to_dict() for c in self.cells],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TableData:
        cells = [TableCell.from_dict(c) for c in data.get("cells", [])]
        loc_data = data.get("location")
        loc = SourceLocation(**loc_data) if loc_data and isinstance(loc_data, dict) else None
        return cls(
            headers=data.get("headers", []),
            rows=data.get("rows", []),
            cells=cells,
            caption=data.get("caption"),
            location=loc,
            table_id=data.get("table_id", ""),
            metadata=data.get("metadata", {}),
        )
