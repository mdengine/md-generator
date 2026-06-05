from __future__ import annotations

from typing import Any

from md_generator.sap.core.link_graph import SapLinkGraph
from md_generator.sap.markdown.builders.abap_sections import (
    format_dynamic_sql_warnings,
    format_joins,
    format_native_sql,
    format_open_sql,
    format_view_refs,
)
from md_generator.sap.markdown.builders.ddic_adapters import (
    data_element_view_from_raw,
    domain_view_from_raw,
    range_type_view_from_raw,
    reference_type_view_from_raw,
    structure_view_from_cds,
    structure_view_from_ddic,
    table_type_view_from_raw,
    table_view_from_raw,
)
from md_generator.sap.markdown.builders.ddic_sections import (
    format_data_element,
    format_ddic_table,
    format_domain,
    format_range_type,
    format_reference_type,
    format_table_type,
)
from md_generator.sap.markdown.builders.renderer_context import RendererContext
from md_generator.sap.markdown.builders.structure_sections import format_structure, format_structure_title
from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject

_DDIC_META_KEYS = frozenset({
    "data_element", "domain", "ddic", "structure", "cds_structure",
    "table_type", "range_type", "reference_type", "adt_ddic",
})


def build_entity_markdown(
    obj: SapObject,
    *,
    relationships: list[dict[str, Any]] | None = None,
    validations: list[dict[str, Any]] | None = None,
    auth_checks: list[dict[str, Any]] | None = None,
    lineage: dict[str, Any] | None = None,
    governance: list[dict[str, Any]] | None = None,
    related_links: list[tuple[str, str]] | None = None,
    link_graph: SapLinkGraph | None = None,
    cap: int = 80,
) -> str:
    rels = (relationships or [])[:cap]
    vals = (validations or [])[:cap]
    auths = (auth_checks or [])[:cap]
    gov = (governance or [])[:cap]
    lin = lineage or {}
    meta = obj.raw_metadata or {}
    abap = meta.get("abap") if isinstance(meta.get("abap"), dict) else None
    ctx = RendererContext(link_graph=link_graph)

    sections = [
        _h1(f"{obj.semantic_entity or obj.name}"),
        _section("Entity Summary", _entity_summary(obj)),
        _section("Business Meaning", _business_meaning(obj)),
        _section("Technical Metadata", _technical_metadata(obj)),
        _section("Relationships", _format_relationships(rels, related_links)),
        _section("Validation Rules", _format_list(vals, "rule_type", "expression")),
        _section("Authorization Rules", _format_auth(auths)),
        _section("Lineage", _format_lineage(lin)),
        _section("Dependencies", _format_dependencies(obj, rels)),
        _section("APIs", _format_apis(obj)),
    ]
    sections.extend(_ddic_sections(obj, ctx))
    if abap:
        warn = format_dynamic_sql_warnings(abap)
        if warn:
            sections.append(_section("SQL Warnings", warn))
        sections.append(_section("Open SQL", format_open_sql(abap)))
        native = format_native_sql(abap)
        if native:
            sections.append(_section("Native SQL", native))
        sections.append(_section("Joins", format_joins(abap)))
    sections.extend([
        _section("Related Tables", _related_tables(obj, rels)),
        _section("Related CDS Views", _related_cds(obj, rels, abap)),
    ])
    if abap:
        sections.append(_section("Views / CDS / HANA References", format_view_refs(abap)))
    sections.append(_section("AI Semantic Tags", _semantic_tags(obj)))
    return "\n\n".join(s for s in sections if s)


def _ddic_sections(obj: SapObject, ctx: RendererContext) -> list[str]:
    meta = obj.raw_metadata or {}
    sections: list[str] = []
    kind = obj.kind

    if kind == SapObjectKind.DATA_ELEMENT and isinstance(meta.get("data_element"), dict):
        view = data_element_view_from_raw(meta["data_element"])
        body = format_data_element(view, ctx)
        if body.strip():
            sections.append(_section("DDIC Data Element", body))

    elif kind == SapObjectKind.DOMAIN and isinstance(meta.get("domain"), dict):
        view = domain_view_from_raw(meta["domain"])
        body = format_domain(view, ctx)
        if body.strip():
            sections.append(_section("DDIC Domain", body))

    elif kind == SapObjectKind.TABLE and isinstance(meta.get("ddic"), dict):
        view = table_view_from_raw(meta["ddic"])
        body = format_ddic_table(view, ctx)
        if body.strip():
            sections.append(_section("DDIC Table Fields", body))

    elif kind == SapObjectKind.STRUCTURE and isinstance(meta.get("structure"), dict):
        view = structure_view_from_ddic(meta["structure"])
        view.name = view.name or obj.name
        view.description = view.description or obj.description or ""
        body = format_structure_title(view) + format_structure(view, ctx)
        sections.append(_section("Structure", body))

    elif kind == SapObjectKind.CDS_STRUCTURE and isinstance(meta.get("cds_structure"), dict):
        view = structure_view_from_cds(meta["cds_structure"])
        view.name = view.name or obj.name
        view.description = view.description or obj.description or ""
        body = format_structure_title(view) + format_structure(view, ctx)
        sections.append(_section("Structure", body))

    elif kind == SapObjectKind.TABLE_TYPE and isinstance(meta.get("table_type"), dict):
        view = table_type_view_from_raw(meta["table_type"])
        body = format_table_type(view, ctx)
        if body.strip():
            sections.append(_section("DDIC Table Type", body))

    elif kind == SapObjectKind.RANGE_TYPE and isinstance(meta.get("range_type"), dict):
        view = range_type_view_from_raw(meta["range_type"])
        body = format_range_type(view, ctx)
        if body.strip():
            sections.append(_section("DDIC Range Type", body))

    elif kind == SapObjectKind.REFERENCE_TYPE and isinstance(meta.get("reference_type"), dict):
        view = reference_type_view_from_raw(meta["reference_type"])
        body = format_reference_type(view, ctx)
        if body.strip():
            sections.append(_section("DDIC Reference Type", body))

    return sections


def _h1(title: str) -> str:
    return f"# {title}\n"


def _section(title: str, body: str) -> str:
    if not body.strip():
        body = "_None identified._"
    return f"## {title}\n\n{body}"


def _entity_summary(obj: SapObject) -> str:
    lines = [
        f"- **Kind:** `{obj.kind.value}`",
        f"- **Name:** `{obj.name}`",
        f"- **Package:** `{obj.package or '—'}`",
        f"- **Object ID:** `{obj.object_id}`",
    ]
    if obj.description:
        lines.append(f"- **Description:** {obj.description}")
    return "\n".join(lines)


def _business_meaning(obj: SapObject) -> str:
    if obj.semantic_entity:
        return f"This artifact represents **{obj.semantic_entity}** in the SAP domain model."
    return "Business meaning inferred from naming conventions and metadata exports."


def _technical_metadata(obj: SapObject) -> str:
    lines = [f"- **Source:** `{obj.source_path}`" if obj.source_path else "- **Source:** _export_"]
    meta = obj.raw_metadata or {}
    adt = meta.get("adt_ddic") if isinstance(meta.get("adt_ddic"), dict) else {}
    if adt.get("ddic_object_kind"):
        lines.append(f"- **DDIC object kind:** `{adt['ddic_object_kind']}`")
    if adt.get("source"):
        lines.append(f"- **ADT source:** `{adt['source']}`")
    for key in sorted(meta.keys()):
        if key in _DDIC_META_KEYS:
            block = meta[key]
            if isinstance(block, dict):
                src = block.get("definition_source", "")
                if src:
                    lines.append(f"- **{key}:** `{src}` definition")
                else:
                    lines.append(f"- **{key}:** structured metadata")
            continue
        if key != "adt_ddic":
            lines.append(f"- **{key}:** metadata block present")
    return "\n".join(lines)


def _format_relationships(
    rels: list[dict[str, Any]],
    links: list[tuple[str, str]] | None,
) -> str:
    lines: list[str] = []
    for r in rels:
        lines.append(f"- `{r.get('relation', 'LINK')}` → {r.get('target_name', r.get('target_id', '?'))}")
    if links:
        lines.append("")
        lines.append("### Cross-links")
        for label, href in links:
            lines.append(f"- [{label}]({href})")
    return "\n".join(lines) if lines else ""


def _format_list(items: list[dict[str, Any]], k1: str, k2: str) -> str:
    if not items:
        return ""
    return "\n".join(f"- **{i.get(k1, 'rule')}:** `{i.get(k2, '')}`" for i in items)


def _format_auth(auths: list[dict[str, Any]]) -> str:
    if not auths:
        return ""
    lines = []
    for a in auths:
        fields = ", ".join(a.get("fields", []))
        lines.append(f"- **{a.get('object', '?')}** ({fields}) at line {a.get('line', '?')}")
    return "\n".join(lines)


def _format_lineage(lin: dict[str, Any]) -> str:
    if not lin:
        return ""
    lines = []
    for u in lin.get("upstream", []):
        lines.append(f"- Upstream: `{u.get('id')}` ({', '.join(u.get('relations', []))})")
    for d in lin.get("downstream", []):
        lines.append(f"- Downstream: `{d.get('id')}` ({', '.join(d.get('relations', []))})")
    return "\n".join(lines)


def _format_dependencies(obj: SapObject, rels: list[dict[str, Any]]) -> str:
    meta = obj.raw_metadata or {}
    lines: list[str] = []
    abap = meta.get("abap")
    if isinstance(abap, dict):
        for fn in abap.get("functions", [])[:40]:
            lines.append(f"- Function module: `{fn}`")
        for inc in abap.get("includes", [])[:40]:
            lines.append(f"- Include: `{inc}`")
    if not lines and rels:
        return _format_relationships(rels, None)
    return "\n".join(lines)


def _format_apis(obj: SapObject) -> str:
    meta = obj.raw_metadata or {}
    if "bapi" in meta:
        return f"- BAPI: `{obj.name}`"
    if "odata" in meta:
        lines = [f"- OData entity `{obj.name}` with {len(meta['odata'].get('properties', []))} properties"]
        analysis = meta.get("odata_analysis") or {}
        for es in analysis.get("entity_sets", [])[:10]:
            lines.append(f"- Entity set: `{es.get('name')}` → `{es.get('entity_type')}`")
        for nav in meta["odata"].get("navigation", [])[:10]:
            lines.append(f"- Nav: `{nav.get('name')}` → `{nav.get('target')}` ({nav.get('multiplicity', '?')})")
        return "\n".join(lines)
    if "odata_entity_set" in meta:
        cap = meta.get("capabilities", {})
        return f"- OData entity set `{obj.name}` → `{meta.get('entity_type')}` CRUD: {cap}"
    return ""


def _related_tables(obj: SapObject, rels: list[dict[str, Any]]) -> str:
    meta = obj.raw_metadata or {}
    lines: list[str] = []
    abap = meta.get("abap")
    if isinstance(abap, dict):
        for t in abap.get("tables", []):
            lines.append(f"- `{t}`")
    for r in rels:
        if "TABLE" in str(r.get("relation", "")):
            lines.append(f"- `{r.get('target_name', r.get('target_id'))}`")
    return "\n".join(dict.fromkeys(lines))


def _related_cds(obj: SapObject, rels: list[dict[str, Any]], abap: dict[str, Any] | None = None) -> str:
    lines = []
    if abap:
        for r in abap.get("view_references", []) or []:
            if r.get("kind") == "cds":
                name = r.get("name", "?")
                path = r.get("resolved_path") or (r.get("resolution") or {}).get("resolved_path")
                if path:
                    lines.append(f"- [{name}]({path})")
                else:
                    lines.append(f"- `{name}`")
    for r in rels:
        if r.get("relation") in ("ASSOCIATION", "COMPOSITION"):
            lines.append(f"- `{r.get('target_name', r.get('target_id'))}`")
    return "\n".join(dict.fromkeys(lines))


def _semantic_tags(obj: SapObject) -> str:
    tags = list(obj.tags)
    if obj.semantic_entity:
        tags.append(f"entity:{obj.semantic_entity}")
    tags.append(f"kind:{obj.kind.value.lower()}")
    return "\n".join(f"- `{t}`" for t in sorted(set(tags)))
