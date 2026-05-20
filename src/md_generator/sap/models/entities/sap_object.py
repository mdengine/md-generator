from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from md_generator.sap.models.entities.kinds import SapObjectKind


@dataclass(slots=True)
class SapObject:
    kind: SapObjectKind
    name: str
    package: str = ""
    description: str = ""
    source_path: Path | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)
    semantic_entity: str = ""
    tags: list[str] = field(default_factory=list)

    @property
    def object_id(self) -> str:
        pkg = self.package or "_"
        return f"{self.kind.value}:{pkg}:{self.name}"

    def slug(self) -> str:
        from md_generator.sap.markdown.builders.slug import slugify_segment

        base = f"{self.package}_{self.name}" if self.package else self.name
        return slugify_segment(base)
