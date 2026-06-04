from __future__ import annotations

from typing import Any

from md_generator.sap.markdown.builders.abap_sections import (
    format_dynamic_sql_warnings,
    format_joins,
    format_native_sql,
    format_open_sql,
    format_view_refs,
)
from md_generator.sap.models.entities.sap_object import SapObject


def build_entity_markdown(
    obj: SapObject,
    *,
    relationships: list[dict[str, Any]] | None = None,
    validations: list[dict[str, Any]] | None = None,
    auth_checks: list[dict[str, Any]] | None = None,
    lineage: dict[str, Any] | None = None,
    governance: list[dict[str, Any]] | None = None,
    related_links: list[tuple[str, str]] | None = None,
    cap: int = 80,
) -> str:
    rels = (relationships or [])[:cap]
    vals = (validations or [])[:cap]
    auths = (auth_checks or [])[:cap]
    gov = (governance or [])[:cap]
    lin = lineage or {}
    abap = (obj.raw_metadata or {}).get("abap") if isinstance((obj.raw_metadata or {}).get("abap"), dict) else None

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
    for key in sorted(meta.keys()):
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
