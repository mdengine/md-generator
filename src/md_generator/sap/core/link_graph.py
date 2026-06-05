from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath

from md_generator.sap.markdown.builders.slug import slugify_segment


def _relpath_md(from_rel: str, to_rel: str) -> str:
    a = PurePosixPath(from_rel).parent
    b = PurePosixPath(to_rel)
    common = 0
    from_parts = a.parts
    to_parts = b.parts
    for x, y in zip(from_parts, to_parts):
        if x != y:
            break
        common += 1
    ups = [".."] * (len(from_parts) - common)
    return "/".join(ups + list(to_parts[common:]))


@dataclass
class SapLinkGraph:
    _paths: dict[tuple[str, str, str], str] = field(default_factory=dict)
    _canonical: dict[tuple[str, str], str] = field(default_factory=dict)
    _entity_for_canonical: dict[str, str] = field(default_factory=dict)

    def register(self, kind: str, package: str, name: str, rel_path: str) -> None:
        self._paths[(kind, package or "", name)] = rel_path.replace("\\", "/")

    def register_canonical(self, kind: str, name: str, canonical_path: str) -> None:
        key = (kind.upper(), name.upper())
        self._canonical[key] = canonical_path.replace("\\", "/")
        entity = self.path_for(kind, "", name) or self.path_for(kind.lower(), "", name)
        if entity:
            self._entity_for_canonical[canonical_path] = entity

    def path_for(self, kind: str, package: str, name: str) -> str | None:
        return self._paths.get((kind, package or "", name))

    def canonical_path_for(self, kind: str, name: str) -> str | None:
        return self._canonical.get((kind.upper(), name.upper()))

    def entity_path_for(self, kind: str, name: str, package: str = "") -> str | None:
        return self.path_for(kind, package, name) or self.path_for(kind.lower(), package, name)

    def bidirectional_links(self, from_rel: str, kind: str, name: str, package: str = "") -> list[tuple[str, str]]:
        links = list(self.related_links(from_rel, kind, package, name))
        canonical = self.canonical_path_for(kind.upper(), name)
        if canonical:
            links.append((f"Canonical: {name}", _relpath_md(from_rel, canonical)))
        entity = self._entity_for_canonical.get(canonical or "")
        if entity and canonical:
            links.append((f"Entity: {name}", _relpath_md(from_rel, entity)))
        return links

    def entity_rel_path(self, package: str, name: str) -> str:
        slug = slugify_segment(f"{package}_{name}" if package else name)
        return f"entities/{slug}.md"

    def related_links(
        self,
        from_rel: str,
        kind: str,
        package: str,
        name: str,
        label: str | None = None,
    ) -> list[tuple[str, str]]:
        target = self.path_for(kind, package, name)
        if not target:
            return []
        lbl = label or (f"{package}.{name}" if package else name)
        return [(lbl, _relpath_md(from_rel, target))]
