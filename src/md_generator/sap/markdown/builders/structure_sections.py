from __future__ import annotations

from md_generator.sap.markdown.builders.ddic_adapters import StructureComponent, StructureView
from md_generator.sap.markdown.builders.renderer_context import (
    RendererContext,
    link_for,
    link_for_type_reference,
    md_link,
)


def format_structure(
    view: StructureView,
    ctx: RendererContext | None = None,
    *,
    alternate_sources: list[str] | None = None,
) -> str:
    lines = [
        f"**Definition source:** `{view.definition_source or '—'}`",
    ]
    if view.package:
        lines.append(f"**Package:** `{view.package}`")
    if view.enhancement_category:
        lines.append(f"**Enhancement category:** `{view.enhancement_category}`")
    lines.extend(["", "## Components", ""])
    lines.append("| Component | Type | Semantic type | Data element |")
    lines.append("|-----------|------|---------------|--------------|")
    for comp in view.components:
        lines.append(_format_component_row(comp, ctx))
    if alternate_sources:
        lines.extend(["", "## Alternate definitions", ""])
        for src in alternate_sources:
            lines.append(f"- {src}")
    return "\n".join(lines) + "\n"


def _format_component_row(comp: StructureComponent, ctx: RendererContext | None) -> str:
    type_name = comp.type_name or "—"
    type_path = link_for_type_reference(comp.type_kind, comp.type_name, ctx) if comp.type_name else None
    de = comp.data_element or "—"
    de_path = link_for("DATA_ELEMENT", comp.data_element, ctx) if comp.data_element else None
    return (
        f"| `{comp.name}` | {md_link(type_name, type_path)} | `{comp.semantic_type.value}` | "
        f"{md_link(de, de_path)} |"
    )


def format_structure_title(view: StructureView) -> str:
    return f"# Structure: {view.name}\n\n**Description:** {view.description or '—'}\n\n"
