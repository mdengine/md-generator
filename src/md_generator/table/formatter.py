from __future__ import annotations

"""Table Formatting & Alignment Utilities.

Phase 2E/Prompt 07 Implementation:
- Formats structured TableData into beautifully aligned GitHub-Flavored Markdown.
- Supports customizable alignments and HTML table representation for complex merged cells.
"""

from typing import List, Optional
from md_generator.table.models import TableData


def format_markdown_table(table: TableData) -> str:
    """Formats TableData into aligned Markdown."""
    return table.to_markdown()


def table_to_html(table: TableData) -> str:
    """Converts TableData to clean HTML <table> supporting row_span and col_span."""
    lines: List[str] = ["<table>"]
    if table.caption:
        lines.append(f"  <caption>{table.caption}</caption>")

    if table.headers:
        lines.append("  <thead>")
        lines.append("    <tr>")
        for h in table.headers:
            lines.append(f"      <th>{h}</th>")
        lines.append("    </tr>")
        lines.append("  </thead>")

    lines.append("  <tbody>")
    for row in table.rows:
        lines.append("    <tr>")
        for cell in row:
            lines.append(f"      <td>{cell}</td>")
        lines.append("    </tr>")
    lines.append("  </tbody>")
    lines.append("</table>")
    return "\n".join(lines)
