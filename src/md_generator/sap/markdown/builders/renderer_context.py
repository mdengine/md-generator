from __future__ import annotations

from dataclasses import dataclass, field

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.core.link_graph import SapLinkGraph
from md_generator.sap.graph.store import ArtifactGraphStore
from md_generator.sap.markdown.resolved_link import ResolvedLink

if False:  # TYPE_CHECKING pattern without import cycle at runtime
    from md_generator.sap.markdown.cross_link_registry import CrossLinkRegistry

PathKey = tuple[str, str]

# Registry keys used in path_registry (kind, UPPER name)
ARTIFACT_TYPE_TO_PATH_KIND: dict[str, str] = {
    "ddic.data_element": "DATA_ELEMENT",
    "ddic.domain": "DOMAIN",
    "ddic.structure": "STRUCTURE",
    "ddic.table": "TABLE",
    "ddic.table_type": "TABLE_TYPE",
    "ddic.range_type": "RANGE_TYPE",
    "ddic.reference_type": "REFERENCE_TYPE",
    "cds.structure": "CDS_STRUCTURE",
}

# Lookup order when resolving a DDIC type_kind + type_name cross-link
TYPE_KIND_TO_PATH_KINDS: dict[str, list[str]] = {
    "domain": ["DOMAIN"],
    "structure": ["STRUCTURE", "CDS_STRUCTURE"],
    "tabletype": ["TABLE_TYPE"],
    "table": ["TABLE"],
    "rangetype": ["RANGE_TYPE"],
    "referencetype": ["REFERENCE_TYPE"],
    "reference": ["REFERENCE_TYPE"],
    "dataelement": ["DATA_ELEMENT"],
}


@dataclass
class RendererContext:
    graph_store: ArtifactGraphStore | None = None
    link_graph: SapLinkGraph | None = None
    path_registry: dict[PathKey, str] = field(default_factory=dict)
    artifact_by_name: dict[str, CanonicalArtifact] | None = None
    current_artifact_id: str = ""
    cross_link_registry: object | None = None  # CrossLinkRegistry
    semantic_narrative: bool = False


def link_for(kind: str, name: str, ctx: RendererContext | None) -> str | None:
    if not ctx or not name:
        return None
    key = (kind.upper(), name.upper())
    return ctx.path_registry.get(key)


def link_for_type_reference(type_kind: str, type_name: str, ctx: RendererContext | None) -> str | None:
    if not ctx or not type_name:
        return None
    tk = type_kind.replace("_", "").lower()
    for kind in TYPE_KIND_TO_PATH_KINDS.get(tk, ["DATA_ELEMENT", "DOMAIN", "STRUCTURE", "CDS_STRUCTURE", "TABLE"]):
        path = link_for(kind, type_name, ctx)
        if path:
            return path
    return link_for("DATA_ELEMENT", type_name, ctx) or link_for("DOMAIN", type_name, ctx)


def md_link(label: str, path: str | None) -> str:
    if path:
        return f"[{label}]({path})"
    return f"`{label}`"


def format_resolved_link(label: str, link: ResolvedLink | None, *, fallback_path: str | None = None) -> str:
    href = link.href if link else fallback_path
    if href:
        if link and link.confidence < 0.6:
            return f"[{label}]({href}) _(low confidence: {link.strategy})_"
        return md_link(label, href)
    if link and link.strategy == "heuristic_label":
        return f"`{label}` _(unresolved)_"
    return f"`{label}`"


def resolve_kind_link(kind: str, name: str, ctx: RendererContext | None) -> str:
    if not name or name == "—":
        return "—"
    reg = ctx.cross_link_registry if ctx else None
    if reg is not None:
        return format_resolved_link(name, reg.resolve_link(kind, name))
    return md_link(name, link_for(kind, name, ctx))


def resolve_type_link(type_kind: str, type_name: str, ctx: RendererContext | None) -> str:
    if not type_name or type_name == "—":
        return "—"
    reg = ctx.cross_link_registry if ctx else None
    if reg is not None:
        return format_resolved_link(type_name, reg.resolve_type_reference(type_kind, type_name))
    return md_link(type_name, link_for_type_reference(type_kind, type_name, ctx))


def build_path_registry(artifacts: list[CanonicalArtifact], output_dir_rel: str = "") -> dict[PathKey, str]:
    """Build (kind, name) -> relative markdown path from artifact list."""
    registry: dict[PathKey, str] = {}
    for artifact in artifacts:
        kind = ARTIFACT_TYPE_TO_PATH_KIND.get(artifact.artifact_type)
        if not kind:
            continue
        slug = artifact.name.lower().replace(" ", "-").replace("/", "-").replace("::", "-")
        path = _artifact_md_path(artifact.artifact_type, slug)
        if output_dir_rel:
            path = f"{output_dir_rel.rstrip('/')}/{path}"
        registry[(kind, artifact.name.upper())] = path
        if artifact.artifact_type in ("ddic.structure", "cds.structure"):
            registry[("STRUCTURE", artifact.name.upper())] = path
    return registry


def _artifact_md_path(artifact_type: str, slug: str) -> str:
    if artifact_type == "ddic.data_element":
        return f"ddic/data-elements/{slug}.md"
    if artifact_type == "ddic.domain":
        return f"ddic/domains/{slug}.md"
    if artifact_type in ("ddic.structure", "cds.structure"):
        return f"structures/{slug}.md"
    if artifact_type == "ddic.table":
        return f"ddic/tables/{slug}.md"
    if artifact_type == "ddic.table_type":
        return f"ddic/table-types/{slug}.md"
    if artifact_type == "ddic.range_type":
        return f"ddic/range-types/{slug}.md"
    if artifact_type == "ddic.reference_type":
        return f"ddic/reference-types/{slug}.md"
    return f"{slug}.md"
