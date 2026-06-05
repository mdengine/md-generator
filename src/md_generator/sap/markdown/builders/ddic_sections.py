from __future__ import annotations

from md_generator.sap.markdown.builders.ddic_adapters import (
    DataElementView,
    DomainView,
    RangeTypeView,
    ReferenceTypeView,
    TableTypeView,
    TableView,
)
from md_generator.sap.markdown.builders.renderer_context import (
    RendererContext,
    link_for,
    link_for_type_reference,
    md_link,
)


def format_data_element(view: DataElementView, ctx: RendererContext | None = None) -> str:
    lines = [
        f"- **Semantic type:** `{view.semantic_type.value}`",
        f"- **Type kind:** `{view.type_kind or '—'}`",
    ]
    type_name = view.type_name or "—"
    type_path = link_for_type_reference(view.type_kind, view.type_name, ctx)
    lines.append(f"- **Type name:** {md_link(type_name, type_path)}")
    lines.extend([
        f"- **Data type:** `{view.data_type or '—'}`",
        f"- **Length:** {view.data_type_length}",
        f"- **Decimals:** {view.data_type_decimals}",
    ])
    if view.resolved_type:
        rt = view.resolved_type
        lines.append(
            f"- **Resolved:** `{rt.get('ddic_object_kind', '?')}` "
            f"({rt.get('resolution_strategy', '—')})"
        )
    body = "\n".join(lines)
    labels = [
        ("Short label", view.short_field_label),
        ("Medium label", view.medium_field_label),
        ("Long label", view.long_field_label),
        ("Heading label", view.heading_field_label),
    ]
    if any(v for _, v in labels):
        body += "\n\n### Field labels\n\n"
        for label, value in labels:
            if value:
                body += f"- **{label}:** {value}\n"
    if view.search_help:
        body += f"\n### Search help\n\n- `{view.search_help}`"
    return body


def format_domain(view: DomainView, ctx: RendererContext | None = None) -> str:
    lines = [
        f"- **Data type:** `{view.data_type or '—'}`",
        f"- **Length:** {view.length}",
        f"- **Decimals:** {view.decimals}",
        f"- **Output length:** {view.output_length}",
    ]
    if view.value_table:
        vt_path = link_for("TABLE", view.value_table, ctx)
        lines.append(f"- **Value table:** {md_link(view.value_table, vt_path)}")
    if view.conversion_routine:
        lines.append(f"- **Conversion routine:** `{view.conversion_routine}`")
    if view.lower_case:
        lines.append("- **Lower case:** yes")
    if view.sign_flag:
        lines.append("- **Sign flag:** yes")
    return "\n".join(lines)


def format_ddic_table(view: TableView, ctx: RendererContext | None = None) -> str:
    lines: list[str] = []
    if view.table_type:
        lines.append(f"**Table type:** `{view.table_type}`")
    if view.definition_source:
        lines.append(f"**Source:** `{view.definition_source}`")
    if lines:
        lines.append("")
    lines.append("| Field | Data element | Semantic type | Key | Check table |")
    lines.append("|-------|--------------|---------------|-----|-------------|")
    for f in view.fields:
        key = "yes" if f.key else ""
        de = f.data_element or "—"
        de_path = link_for("DATA_ELEMENT", de, ctx) if de != "—" else None
        ct = f.check_table or ""
        ct_path = link_for("TABLE", ct, ctx) if ct else None
        lines.append(
            f"| `{f.name}` | {md_link(de, de_path)} | `{f.semantic_type.value}` | {key} | "
            f"{md_link(ct, ct_path) if ct else ''} |"
        )
    return "\n".join(lines)


def format_table_type(view: TableTypeView, ctx: RendererContext | None = None) -> str:
    row_path = link_for_type_reference("structure", view.row_type, ctx)
    line_path = link_for_type_reference("tableType", view.line_type, ctx)
    lines = [
        f"- **Row type:** {md_link(view.row_type or '—', row_path)}",
        f"- **Line type:** {md_link(view.line_type or '—', line_path)}",
        f"- **Access mode:** `{view.access_mode or '—'}`",
    ]
    if view.primary_key:
        lines.extend(["", "### Primary key", ""] + [f"- `{k}`" for k in view.primary_key])
    return "\n".join(lines)


def format_range_type(view: RangeTypeView, ctx: RendererContext | None = None) -> str:
    de_path = link_for("DATA_ELEMENT", view.data_element, ctx)
    dom_path = link_for("DOMAIN", view.domain, ctx)
    return "\n".join([
        f"- **Data element:** {md_link(view.data_element or '—', de_path)}",
        f"- **Domain:** {md_link(view.domain or '—', dom_path)}",
        f"- **Length:** {view.length}",
        f"- **Decimals:** {view.decimals}",
    ])


def format_reference_type(view: ReferenceTypeView, ctx: RendererContext | None = None) -> str:
    ref_path = link_for_type_reference("referenceType", view.referenced_type, ctx)
    ct_path = link_for("TABLE", view.check_table, ctx)
    return "\n".join([
        f"- **Referenced type:** {md_link(view.referenced_type or '—', ref_path)}",
        f"- **Check table:** {md_link(view.check_table or '—', ct_path)}",
    ])
