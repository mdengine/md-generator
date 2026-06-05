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
    resolve_kind_link,
    resolve_type_link,
)


def format_data_element(view: DataElementView, ctx: RendererContext | None = None) -> str:
    lines = [
        f"- **Semantic type:** `{view.semantic_type.value}`",
        f"- **Type kind:** `{view.type_kind or '—'}`",
    ]
    type_name = view.type_name or "—"
    lines.append(f"- **Type name:** {resolve_type_link(view.type_kind, view.type_name, ctx)}")
    lines.extend([
        f"- **Data type:** `{view.data_type or '—'}`",
        f"- **Length:** {view.data_type_length}",
        f"- **Decimals:** {view.data_type_decimals}",
    ])
    if view.resolved_type:
        rt = view.resolved_type
        conf = rt.get("confidence")
        conf_txt = f", confidence {conf:.2f}" if conf is not None else ""
        lines.append(
            f"- **Resolved:** `{rt.get('ddic_object_kind', '?')}` "
            f"({rt.get('resolution_strategy', '—')}{conf_txt})"
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
        lines.append(f"- **Value table:** {resolve_kind_link('TABLE', view.value_table, ctx)}")
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
        ct = f.check_table or ""
        lines.append(
            f"| `{f.name}` | {resolve_kind_link('DATA_ELEMENT', de, ctx)} | `{f.semantic_type.value}` | {key} | "
            f"{resolve_kind_link('TABLE', ct, ctx) if ct else ''} |"
        )
    return "\n".join(lines)


def format_table_type(view: TableTypeView, ctx: RendererContext | None = None) -> str:
    lines = [
        f"- **Row type:** {resolve_type_link('structure', view.row_type, ctx)}",
        f"- **Line type:** {resolve_type_link('tableType', view.line_type, ctx)}",
        f"- **Access mode:** `{view.access_mode or '—'}`",
    ]
    if view.primary_key:
        lines.extend(["", "### Primary key", ""] + [f"- `{k}`" for k in view.primary_key])
    return "\n".join(lines)


def format_range_type(view: RangeTypeView, ctx: RendererContext | None = None) -> str:
    return "\n".join([
        f"- **Data element:** {resolve_kind_link('DATA_ELEMENT', view.data_element, ctx)}",
        f"- **Domain:** {resolve_kind_link('DOMAIN', view.domain, ctx)}",
        f"- **Length:** {view.length}",
        f"- **Decimals:** {view.decimals}",
    ])


def format_reference_type(view: ReferenceTypeView, ctx: RendererContext | None = None) -> str:
    return "\n".join([
        f"- **Referenced type:** {resolve_type_link('referenceType', view.referenced_type, ctx)}",
        f"- **Check table:** {resolve_kind_link('TABLE', view.check_table, ctx)}",
    ])
