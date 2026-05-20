from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from md_generator.sap.models.entities.sap_object import SapObject


@dataclass
class ParseContext:
    root: Path
    package_hint: str = ""


@dataclass
class SapParseResult:
    path: Path
    objects: list[SapObject] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class SapParserPlugin(Protocol):
    name: str

    def can_parse(self, path: Path) -> bool: ...

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult: ...
