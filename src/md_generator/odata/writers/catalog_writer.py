from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from md_generator.odata.models.domain import ODataMetadataDocument


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def render_odata_catalog(
    root: Path,
    documents: list[ODataMetadataDocument],
    *,
    on_file: Callable[[Path], None] | None = None,
) -> None:
    if not documents:
        return
    odata_root = root / "odata"
    index_lines = [
        "# OData Service Catalog",
        "",
        "Bootstrap index for AI/RAG ingestion.",
        "",
        "## Services",
        "",
    ]
    for doc in documents:
        svc_slug = _slug(doc.service_name)
        index_lines.append(f"- [{doc.service_name}](services/{svc_slug}.md) — OData {doc.odata_version.value}")
        svc_md = _render_service(doc)
        p = odata_root / "services" / f"{svc_slug}.md"
        write_text(p, svc_md)
        if on_file:
            on_file(p)
        for es in doc.entity_sets:
            es_slug = _slug(es.name)
            es_md = _render_entity_set(doc, es)
            ep = odata_root / "entity-sets" / f"{svc_slug}_{es_slug}.md"
            write_text(ep, es_md)
            if on_file:
                on_file(ep)
            index_lines.append(f"  - Entity set: [{es.name}](entity-sets/{svc_slug}_{es_slug}.md) → `{es.entity_type}`")
        for entity in doc.entity_types:
            et_slug = _slug(entity.name)
            et_md = _render_entity_type(doc, entity)
            tp = odata_root / "entity-types" / f"{svc_slug}_{et_slug}.md"
            write_text(tp, et_md)
            if on_file:
                on_file(tp)
        for action in doc.actions:
            a_slug = _slug(action.name)
            am = _render_action(doc, action)
            ap = odata_root / "actions" / f"{svc_slug}_{a_slug}.md"
            write_text(ap, am)
            if on_file:
                on_file(ap)
            index_lines.append(f"  - Action: [{action.name}](actions/{svc_slug}_{a_slug}.md)")
        for fn in doc.functions:
            f_slug = _slug(fn.name)
            fm = _render_function(doc, fn)
            fp = odata_root / "functions" / f"{svc_slug}_{f_slug}.md"
            write_text(fp, fm)
            if on_file:
                on_file(fp)
    index_lines.extend(["", "## Version summary", ""])
    versions = sorted({d.odata_version.value for d in documents})
    for v in versions:
        index_lines.append(f"- OData **{v}**")
    write_text(odata_root / "index.md", "\n".join(index_lines) + "\n")
    if on_file:
        on_file(odata_root / "index.md")


def _slug(name: str) -> str:
    from md_generator.odata.writers.slug import slugify_segment

    return slugify_segment(name)


def _render_service(doc: ODataMetadataDocument) -> str:
    lines = [
        f"# OData Service: {doc.service_name}",
        "",
        f"- **Version:** {doc.odata_version.value}",
        f"- **Namespace:** `{doc.default_namespace}`",
        f"- **Container:** `{doc.container_name}`",
        f"- **Metadata URL:** `{doc.metadata_url}`",
        f"- **Service root:** `{doc.service_root or '—'}`",
        "",
        "## Entity sets",
        "",
    ]
    for es in doc.entity_sets:
        lines.append(f"- `{es.name}` → `{es.entity_type}`")
    lines.extend(["", "## Entity types", ""])
    for et in doc.entity_types:
        lines.append(f"- `{et.name}` ({len(et.properties)} properties)")
    return "\n".join(lines)


def _render_entity_set(doc: ODataMetadataDocument, es) -> str:
    cap = es.capabilities
    opts = cap.supported_query_options(doc.odata_version)
    lines = [
        f"# Entity Set: {es.name}",
        "",
        f"- **Entity type:** `{es.entity_type}`",
        f"- **Service:** `{doc.service_name}`",
        "",
        "## CRUD capabilities",
        "",
        f"- Insert: {cap.insertable if cap.insertable is not None else 'unknown'}",
        f"- Update: {cap.updatable if cap.updatable is not None else 'unknown'}",
        f"- Delete: {cap.deletable if cap.deletable is not None else 'unknown'}",
        "",
        "## Supported Query Options",
        "",
    ]
    for o in opts:
        lines.append(f"- `{o}`")
    return "\n".join(lines)


def _render_entity_type(doc: ODataMetadataDocument, entity) -> str:
    lines = [
        f"# Entity Type: {entity.name}",
        "",
        f"- **Namespace:** `{entity.namespace}`",
        "",
        "## Properties",
        "",
    ]
    for p in entity.properties:
        lines.append(f"- `{p.name}` : `{p.type_name}`")
    if entity.navigation_properties:
        lines.extend(["", "## Navigation properties", ""])
        for n in entity.navigation_properties:
            lines.append(f"- `{n.name}` → `{n.target_type}` ({n.multiplicity})")
    return "\n".join(lines)


def _render_action(doc: ODataMetadataDocument, action) -> str:
    return "\n".join(
        [
            f"# Action: {action.name}",
            "",
            f"- **Bound:** {action.is_bound}",
            f"- **Service:** `{doc.service_name}`",
        ]
    )


def _render_function(doc: ODataMetadataDocument, fn) -> str:
    return "\n".join(
        [
            f"# Function: {fn.name}",
            "",
            f"- **Return type:** `{fn.return_type or '—'}`",
            f"- **Service:** `{doc.service_name}`",
        ]
    )
