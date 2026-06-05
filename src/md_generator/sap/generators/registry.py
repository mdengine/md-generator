from __future__ import annotations

import json
from pathlib import Path

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.transformation.graph import TransformationGraph
from md_generator.sap.markdown.builders.abap_sections import build_abap_program_markdown
from md_generator.sap.generators.lineage.from_graph import generate_impact_markdown, generate_lineage_json
from md_generator.sap.generators.mermaid.transformation_graph import render_transformation_mermaid
from md_generator.sap.graph.store import ArtifactGraphStore


class GeneratorRegistry:
    def __init__(self) -> None:
        self._generators: dict[str, object] = {}

    def register(self, artifact_type: str, fn: object) -> None:
        self._generators[artifact_type] = fn

    def generate_all(
        self,
        artifacts: list[CanonicalArtifact],
        store: ArtifactGraphStore,
        output_dir: Path,
    ) -> list[Path]:
        written: list[Path] = []
        for artifact in artifacts:
            fn = self._generators.get(artifact.artifact_type, _default_generate)
            paths = fn(artifact, store, output_dir)  # type: ignore[operator]
            written.extend(paths)
        return written


def default_generator_registry() -> GeneratorRegistry:
    reg = GeneratorRegistry()
    reg.register("hana.calculation_view", _generate_hana_cv)
    reg.register("hana.analytic_view", _generate_hana_cv)
    reg.register("hana.attribute_view", _generate_hana_cv)
    reg.register("hana.hdi_calculation_view", _generate_hana_cv)
    reg.register("hana.sql_view", _generate_hana_cv)
    reg.register("cds.view", _generate_cds)
    reg.register("ddic.table", _generate_ddic)
    reg.register("abap.program", _generate_abap)
    reg.register("odata.entity", _generate_odata)
    for bw_type in ("bw.adso", "bw.composite_provider", "bw.transformation", "bw.dtp", "bw.info_object"):
        reg.register(bw_type, _generate_bw)
    for ds_type in ("datasphere.analytical_model", "datasphere.view", "datasphere.data_flow"):
        reg.register(ds_type, _generate_datasphere)
    return reg


from md_generator.sap.framework.paths import safe_filename


def _slug(name: str) -> str:
    return name.lower().replace(" ", "-").replace("/", "-").replace("::", "-")


def _write_canonical_json(artifact: CanonicalArtifact, output_dir: Path) -> Path:
    fname = safe_filename(artifact.identity.stable_id, ".json")
    path = output_dir / "json" / "canonical" / fname
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact.model_dump(mode="json"), indent=2), encoding="utf-8")
    return path


def _default_generate(artifact: CanonicalArtifact, store: ArtifactGraphStore, output_dir: Path) -> list[Path]:
    return [_write_canonical_json(artifact, output_dir)]


def _hana_list(meta: dict, artifact: CanonicalArtifact, key: str) -> list:
    val = meta.get(key)
    if val:
        return list(val)
    top = getattr(artifact, key, None)
    return list(top) if top else []


def _build_hana_cv_markdown(artifact: CanonicalArtifact) -> str:
    meta = artifact.metadata or {}
    semantics = meta.get("semantics") or getattr(artifact, "semantics", {}) or {}
    findings = meta.get("rule_findings", [])
    lines = [
        f"# {artifact.name}",
        "",
        f"**Type:** HANA Calculation View",
        f"**Schema:** {artifact.schema or '—'}",
        f"**Package:** {artifact.package or '—'}",
    ]
    if semantics.get("description"):
        lines.extend(["", f"**Description:** {semantics['description']}"])
    if semantics.get("data_category"):
        lines.append(f"**Data category:** {semantics['data_category']}")
    if semantics.get("scenario_type"):
        lines.append(f"**Scenario type:** {semantics['scenario_type']}")

    lines.extend(["", "## Input parameters / variables", ""])
    params = _hana_list(meta, artifact, "input_parameters")
    variables = _hana_list(meta, artifact, "variables")
    if params:
        for p in params:
            lines.append(f"- `{p.get('name', p)}` ({p.get('data_type', '')})")
    elif variables:
        for v in variables:
            label = v.get("default_value") or v.get("name", v)
            lines.append(f"- `{v.get('name', v)}` — {label}")
    else:
        lines.append("_None identified._")

    lines.extend(["", "## Data sources", ""])
    data_sources = _hana_list(meta, artifact, "data_sources")
    if data_sources:
        for ds in data_sources:
            schema = ds.get("schema", "")
            name = ds.get("name", ds)
            obj_type = ds.get("object_type", "table")
            ref = f"{schema}.{name}" if schema else str(name)
            lines.append(f"- `{ref}` ({obj_type})")
    else:
        lines.append("_None identified._")

    lines.extend(["", "## Transformation steps", ""])
    steps = meta.get("calculation_views") or []
    if steps:
        for step in steps:
            step_id = step.get("id", "")
            kind = step.get("kind", "step")
            inputs = step.get("inputs") or []
            input_txt = ", ".join(f"`{i}`" for i in inputs) if inputs else "—"
            lines.append(f"### {step_id} ({kind})")
            lines.append(f"- **Inputs:** {input_txt}")
            if kind == "join":
                keys = step.get("join_keys") or []
                key_txt = ", ".join(f"`{k}`" for k in keys) if keys else "—"
                lines.append(f"- **Join:** {step.get('join_type', 'inner')} on {key_txt}")
            if step.get("filter"):
                lines.append(f"- **Filter:** `{step['filter']}`")
            cols = step.get("columns") or []
            if cols:
                preview = ", ".join(f"`{c}`" for c in cols[:12])
                if len(cols) > 12:
                    preview += f", … (+{len(cols) - 12} more)"
                lines.append(f"- **Columns:** {preview}")
            lines.append("")
    else:
        lines.append("_None identified._")

    lines.extend(["", "## Output attributes (logical model)", ""])
    logical = meta.get("logical_attributes") or []
    if logical:
        for attr in sorted(logical, key=lambda a: int(a.get("order") or 0)):
            desc = attr.get("description") or ""
            suffix = f" — {desc}" if desc else ""
            lines.append(f"- `{attr.get('name', attr)}`{suffix}")
    else:
        attrs = _hana_list(meta, artifact, "attributes")
        if attrs:
            seen: set[str] = set()
            for attr in attrs:
                name = attr.get("name", attr)
                if name in seen:
                    continue
                seen.add(name)
                dtype = attr.get("data_type", "")
                suffix = f" ({dtype})" if dtype else ""
                lines.append(f"- `{name}`{suffix}")
        else:
            lines.append("_None identified._")

    lines.extend(["", "## Calculated columns", ""])
    calculated = _hana_list(meta, artifact, "calculated_columns")
    if calculated:
        for col in calculated:
            expr = col.get("expression", "")
            if expr:
                lines.append(f"- `{col.get('name', col)}`: `{expr}`")
            else:
                lines.append(f"- `{col.get('name', col)}`")
    else:
        lines.append("_None identified._")

    lines.extend(["", "## Measures", ""])
    measures = _hana_list(meta, artifact, "measures")
    if measures:
        for measure in measures:
            agg = measure.get("aggregation", "")
            suffix = f" ({agg})" if agg else ""
            lines.append(f"- `{measure.get('name', measure)}`{suffix}")
    else:
        lines.append("_None identified._")

    if findings:
        lines.extend(["", "## Optimization findings", ""])
        for f in findings:
            lines.append(f"- [{f.get('severity', 'info')}] {f.get('message', '')}")

    return "\n".join(lines) + "\n"


def _generate_hana_cv(artifact: CanonicalArtifact, store: ArtifactGraphStore, output_dir: Path) -> list[Path]:
    slug = _slug(artifact.name if not artifact.package else f"{artifact.package}#{artifact.name}")
    paths = [_write_canonical_json(artifact, output_dir)]
    md_path = output_dir / "hana" / "calculation-views" / f"{slug}.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(_build_hana_cv_markdown(artifact), encoding="utf-8")
    paths.append(md_path)
    paths.append(render_transformation_mermaid(artifact, output_dir / "hana" / "diagrams" / f"{slug}.mmd"))
    paths.append(_write_hana_sql(artifact, output_dir / "hana" / "sql" / f"{slug}.sql"))
    paths.append(generate_lineage_json(artifact, store, output_dir / "hana" / "lineage" / f"{slug}.json"))
    paths.append(generate_impact_markdown(artifact, store, output_dir / "hana" / "impact" / f"{slug}.md"))
    return paths


def _write_hana_sql(artifact: CanonicalArtifact, path: Path) -> Path:
    tg_data = artifact.metadata.get("transformation_graph")
    lines = [f"-- SQL equivalent for {artifact.name}", ""]
    if tg_data:
        tg = TransformationGraph.model_validate(tg_data)
        ordered = tg.topological_order()
        if not ordered:
            ordered = list(tg.nodes.keys())
        for nid in ordered:
            node = tg.nodes[nid]
            if node.node_kind == "source":
                obj = node.properties.get("object_name", node.node_id)
                lines.append(f"-- SOURCE: {obj}")
            elif node.node_kind == "join":
                jt = node.properties.get("join_type", "inner")
                keys = node.properties.get("join_keys", [])
                key_txt = ", ".join(keys) if keys else "—"
                lines.append(f"-- JOIN ({jt}) {nid} ON {key_txt}")
            elif node.node_kind == "aggregate":
                cols = node.properties.get("columns", ["*"])
                lines.append(f"-- AGGREGATE {nid}: {', '.join(cols)}")
            elif node.node_kind == "filter":
                expr = node.properties.get("expression", node.expression if hasattr(node, "expression") else "")
                lines.append(f"-- FILTER: {expr}")
            elif node.node_kind == "projection":
                cols = node.properties.get("columns", ["*"])
                filt = node.properties.get("filter", "")
                if filt:
                    lines.append(f"-- PROJECTION {nid} WHERE {filt}")
                lines.append(f"SELECT {', '.join(cols)} FROM {nid};")
    else:
        schema = artifact.schema or "_SYS_BIC"
        lines.append(f'SELECT * FROM "{schema}"."{artifact.package}/{artifact.name}";')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _generate_cds(artifact: CanonicalArtifact, store: ArtifactGraphStore, output_dir: Path) -> list[Path]:
    slug = _slug(artifact.name)
    paths = [_write_canonical_json(artifact, output_dir)]
    md = output_dir / "cds" / "views" / f"{slug}.md"
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(f"# CDS View: {artifact.name}\n\nPackage: {artifact.package}\n", encoding="utf-8")
    paths.append(md)
    paths.append(render_transformation_mermaid(artifact, output_dir / "cds" / "diagrams" / f"{slug}.mmd"))
    paths.append(generate_lineage_json(artifact, store, output_dir / "cds" / "lineage" / f"{slug}.json"))
    return paths


def _generate_ddic(artifact: CanonicalArtifact, store: ArtifactGraphStore, output_dir: Path) -> list[Path]:
    slug = _slug(artifact.name)
    paths = [_write_canonical_json(artifact, output_dir)]
    md = output_dir / "ddic" / "tables" / f"{slug}.md"
    md.parent.mkdir(parents=True, exist_ok=True)
    fields = artifact.metadata.get("ddic", {}).get("fields", [])
    lines = [f"# DDIC Table: {artifact.name}", "", "## Fields", ""]
    for f in fields:
        lines.append(f"- {f.get('name')} ({f.get('type', '')})")
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    paths.append(md)
    paths.append(generate_impact_markdown(artifact, store, output_dir / "ddic" / "impact" / f"{slug}.md"))
    return paths


def _generate_abap(artifact: CanonicalArtifact, store: ArtifactGraphStore, output_dir: Path) -> list[Path]:
    slug = _slug(artifact.name)
    paths = [_write_canonical_json(artifact, output_dir)]
    md = output_dir / "abap" / "programs" / f"{slug}.md"
    md.parent.mkdir(parents=True, exist_ok=True)
    meta = artifact.metadata.get("abap", {})
    md.write_text(build_abap_program_markdown(artifact.name, meta), encoding="utf-8")
    paths.append(md)
    paths.append(generate_lineage_json(artifact, store, output_dir / "abap" / "lineage" / f"{slug}.json"))
    return paths


def _generate_odata(artifact: CanonicalArtifact, store: ArtifactGraphStore, output_dir: Path) -> list[Path]:
    return [_write_canonical_json(artifact, output_dir)]


def _generate_bw(artifact: CanonicalArtifact, store: ArtifactGraphStore, output_dir: Path) -> list[Path]:
    slug = _slug(artifact.name)
    kind = artifact.artifact_type.replace("bw.", "")
    paths = [_write_canonical_json(artifact, output_dir)]
    md = output_dir / "bw" / kind.replace("_", "-") / f"{slug}.md"
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(f"# BW {artifact.artifact_type}: {artifact.name}\n", encoding="utf-8")
    paths.append(md)
    paths.append(render_transformation_mermaid(artifact, output_dir / "bw" / "diagrams" / f"{slug}.mmd"))
    paths.append(generate_lineage_json(artifact, store, output_dir / "bw" / "lineage" / f"{slug}.json"))
    paths.append(generate_impact_markdown(artifact, store, output_dir / "bw" / "impact" / f"{slug}.md"))
    return paths


def _generate_datasphere(artifact: CanonicalArtifact, store: ArtifactGraphStore, output_dir: Path) -> list[Path]:
    slug = _slug(artifact.name)
    kind = artifact.artifact_type.replace("datasphere.", "")
    paths = [_write_canonical_json(artifact, output_dir)]
    md = output_dir / "datasphere" / kind.replace("_", "-") / f"{slug}.md"
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(f"# Datasphere {artifact.artifact_type}: {artifact.name}\n", encoding="utf-8")
    paths.append(md)
    paths.append(generate_lineage_json(artifact, store, output_dir / "datasphere" / "lineage" / f"{slug}.json"))
    return paths
