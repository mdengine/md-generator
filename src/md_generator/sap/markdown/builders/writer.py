from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from md_generator.sap.core.export_manifest import ExportManifestBuilder
from md_generator.sap.core.link_graph import SapLinkGraph
from md_generator.sap.core.run_config import SapRunConfig
from md_generator.sap.markdown.builders.entity_builder import build_entity_markdown
from md_generator.sap.models.entities.sap_object import SapObject


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def render_all(
    root: Path,
    objects: list[SapObject],
    cfg: SapRunConfig,
    *,
    relationships: dict[str, list[dict[str, Any]]] | None = None,
    validations: list[dict[str, Any]] | None = None,
    auth_checks: list[dict[str, Any]] | None = None,
    lineage: dict[str, list[dict[str, Any]]] | None = None,
    governance: list[dict[str, Any]] | None = None,
    link_graph: SapLinkGraph | None = None,
    manifest: ExportManifestBuilder | None = None,
) -> SapLinkGraph:
    lg = link_graph or SapLinkGraph()
    feats = cfg.effective_features()
    rels_map = relationships or {}
    lin_map = lineage or {}

    write_text(root / "README.md", _readme(objects, cfg))

    val_by_prog: dict[str, list[dict]] = {}
    for v in validations or []:
        val_by_prog.setdefault(v.get("source", ""), []).append(v)
    auth_by_prog: dict[str, list[dict]] = {}
    for a in auth_checks or []:
        auth_by_prog.setdefault(a.get("program", ""), []).append(a)
    gov_by_obj: dict[str, list[dict]] = {}
    for g in governance or []:
        gov_by_obj.setdefault(g.get("object_id", ""), []).append(g)

    for obj in objects:
        rel_path = lg.entity_rel_path(obj.package, obj.name)
        lg.register(obj.kind.value, obj.package, obj.name, rel_path)
        obj_rels = rels_map.get(obj.object_id, [])
        obj_lin = (lin_map.get(obj.object_id) or [{}])[0]
        obj_gov = gov_by_obj.get(obj.object_id, [])
        links: list[tuple[str, str]] = []
        if cfg.markdown_cross_links and link_graph:
            for r in obj_rels[: cfg.performance.intelligence_list_cap]:
                tid = r.get("target_id", "")
                # links filled in second pass
                pass

        md = build_entity_markdown(
            obj,
            relationships=obj_rels,
            validations=val_by_prog.get(obj.name, []),
            auth_checks=auth_by_prog.get(obj.name, []),
            lineage=obj_lin,
            governance=obj_gov,
            related_links=links,
            cap=cfg.performance.intelligence_list_cap,
        )

        if "entities" in feats:
            p = root / rel_path
            write_text(p, md)
            if manifest:
                manifest.add_file(p, root)
                manifest.bump("entities")

        if "technical" in feats:
            p = root / "technical" / Path(rel_path).name
            write_text(p, md)
            if manifest:
                manifest.add_file(p, root)

        if "functional" in feats:
            p = root / "functional" / Path(rel_path).name
            write_text(p, _functional_variant(obj, md))
            if manifest:
                manifest.add_file(p, root)

        if "governance" in feats and obj_gov:
            p = root / "governance" / Path(rel_path).name
            write_text(p, _governance_md(obj, obj_gov))
            if manifest:
                manifest.add_file(p, root)

        if "authorization" in feats and auth_by_prog.get(obj.name):
            p = root / "authorization" / Path(rel_path).name
            write_text(p, _auth_md(obj, auth_by_prog[obj.name]))
            if manifest:
                manifest.add_file(p, root)

        if "lineage" in feats and obj_lin:
            p = root / "lineage" / Path(rel_path).name
            write_text(p, f"# Lineage: {obj.name}\n\n```json\n{json.dumps(obj_lin, indent=2)}\n```\n")
            if manifest:
                manifest.add_file(p, root)

        if "relationships" in feats and obj_rels:
            p = root / "relationships" / Path(rel_path).name
            write_text(p, f"# Relationships: {obj.name}\n\n" + "\n".join(f"- {r}" for r in obj_rels))
            if manifest:
                manifest.add_file(p, root)

        if "json_output" in feats:
            p = root / "json" / f"{obj.slug()}.json"
            write_text(p, json.dumps(obj.raw_metadata, indent=2, default=str))
            if manifest:
                manifest.add_file(p, root)

    if governance:
        gp = root / "governance" / "fields.json"
        write_text(gp, json.dumps(governance, indent=2))
        if manifest:
            manifest.add_file(gp, root)

    return lg


def _readme(objects: list[SapObject], cfg: SapRunConfig) -> str:
    kinds: dict[str, int] = {}
    for o in objects:
        kinds[o.kind.value] = kinds.get(o.kind.value, 0) + 1
    lines = [
        "# SAP Knowledge Pack",
        "",
        f"Generated from {len(cfg.input_paths)} input path(s).",
        "",
        "## Object counts",
        "",
    ]
    for k, n in sorted(kinds.items()):
        lines.append(f"- **{k}:** {n}")
    lines.extend(["", "## Output layout", "", "- `entities/` — AI-ready entity documentation", "- `governance/` — field classifications", "- `relationships/` — graph-derived links", ""])
    return "\n".join(lines)


def _functional_variant(obj: SapObject, base_md: str) -> str:
    return f"# Functional: {obj.semantic_entity or obj.name}\n\n" + base_md.split("## Business Meaning", 1)[-1] if "## Business Meaning" in base_md else base_md


def _governance_md(obj: SapObject, gov: list[dict]) -> str:
    lines = [f"# Governance: {obj.name}", ""]
    for g in gov:
        lines.append(f"- `{g.get('field')}` → **{g.get('classification')}**")
    return "\n".join(lines)


def _auth_md(obj: SapObject, auths: list[dict]) -> str:
    lines = [f"# Authorization: {obj.name}", ""]
    for a in auths:
        lines.append(f"- Object `{a.get('object')}` fields: {', '.join(a.get('fields', []))}")
    return "\n".join(lines)
