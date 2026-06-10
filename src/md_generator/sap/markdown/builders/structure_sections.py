from __future__ import annotations

from md_generator.sap.markdown.builders.ddic_adapters import StructureComponent, StructureView
from md_generator.sap.markdown.builders.renderer_context import (
    RendererContext,
    resolve_kind_link,
    resolve_type_link,
)

_MAX_TREE_DEPTH = 6


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
    has_nested = any(c.children or c.type_kind.lower() == "structure" for c in view.components)
    lines.extend(["", "## Components", ""])
    if has_nested:
        for comp in view.components:
            lines.extend(_format_component_tree(comp, ctx, depth=0, visited_stable_ids=set()))
    else:
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
    de = comp.data_element or "—"
    return (
        f"| `{comp.name}` | {resolve_type_link(comp.type_kind, comp.type_name, ctx)} | "
        f"`{comp.semantic_type.value}` | {resolve_kind_link('DATA_ELEMENT', de, ctx)} |"
    )


def _format_component_tree(
    comp: StructureComponent,
    ctx: RendererContext | None,
    *,
    depth: int,
    visited_stable_ids: set[str],
) -> list[str]:
    if depth >= _MAX_TREE_DEPTH:
        return [f"{'  ' * depth}- `{comp.name}` _(max depth reached)_"]
    indent = "  " * depth
    type_label = comp.type_name or comp.data_element or "—"
    if comp.cycle_detected and comp.cycle_path:
        path = " → ".join(comp.cycle_path)
        return [f"{indent}- `{comp.name}` _Circular reference: {path} (truncated)_"]
    struct_key = (comp.include_structure or comp.type_name or "").upper()
    if struct_key and struct_key in visited_stable_ids:
        return [f"{indent}- `{comp.name}` _Circular reference: {struct_key} (truncated)_"]
    next_visited = set(visited_stable_ids)
    if struct_key:
        next_visited.add(struct_key)
    type_link = resolve_type_link(comp.type_kind, comp.type_name, ctx) if comp.type_name else f"`{type_label}`"
    de_link = resolve_kind_link("DATA_ELEMENT", comp.data_element, ctx) if comp.data_element else ""
    line = f"{indent}- `{comp.name}`: {type_link} ({comp.semantic_type.value})"
    if de_link and de_link != "—":
        line += f", DE {de_link}"
    lines = [line]
    for child in comp.children:
        lines.extend(_format_component_tree(child, ctx, depth=depth + 1, visited_stable_ids=next_visited))
    return lines


def format_structure_title(view: StructureView) -> str:
    return f"# Structure: {view.name}\n\n**Description:** {view.description or '—'}\n\n"
