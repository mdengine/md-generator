"""Export warning collection for Elasticsearch markdown runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ExportWarning:
    code: str
    message: str
    file: str | None = None


@dataclass
class ExportWarningCollector:
    """Accumulates export warnings for per-doc sections and manifest output."""

    _items: list[ExportWarning] = field(default_factory=list)

    def add(
        self,
        code: str,
        message: str,
        *,
        file: str | None = None,
    ) -> None:
        self._items.append(ExportWarning(code=code, message=message, file=file))

    def add_messages(
        self,
        messages: list[str],
        *,
        file: str | None = None,
        code: str = "export_warning",
    ) -> None:
        for message in messages:
            self.add(code, message, file=file)

    def messages_for_file(self, file: str) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for w in self._items:
            if w.file is not None and w.file != file:
                continue
            if w.message not in seen:
                seen.add(w.message)
                out.append(w.message)
        return out

    def to_manifest_list(self) -> list[dict[str, Any]]:
        return [
            {
                "code": w.code,
                "message": w.message,
                **({"file": w.file} if w.file else {}),
            }
            for w in self._items
        ]

    def __bool__(self) -> bool:
        return bool(self._items)


def format_export_warnings_section(messages: list[str]) -> str:
    if not messages:
        return ""
    lines = ["## Export Warnings\n\n"]
    for msg in messages:
        lines.append(f"- {msg}\n")
    lines.append("\n")
    return "".join(lines)


def finalize_markdown_with_warnings(body: str, messages: list[str]) -> str:
    """Append export warnings when present (after main content)."""
    section = format_export_warnings_section(messages)
    if not section:
        return body
    return body.rstrip() + "\n\n" + section
