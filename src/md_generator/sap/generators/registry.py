from __future__ import annotations

import json
from pathlib import Path

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.transformation.graph import TransformationGraph
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
    reg.register("cds.view", _generate_cds)
    reg.register("ddic.table", _generate_ddic)
    reg.register("abap.program", _generate_abap)
    reg.register("odata.entity", _generate_odata)
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


def _generate_hana_cv(artifact: CanonicalArtifact, store: ArtifactGraphStore, output_dir: Path) -> list[Path]:
    slug = _slug(artifact.name)
    paths = [_write_canonical_json(artifact, output_dir)]
    md_path = output_dir / "hana" / "calculation-views" / f"{slug}.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    findings = artifact.metadata.get("rule_findings", [])
    md_lines = [
        f"# {artifact.name}",
        "",
        f"**Type:** HANA Calculation View",
        f"**Schema:** {artifact.schema}",
        f"**Package:** {artifact.package}",
        "",
        "## Data sources",
        "",
    ]
    for ds in artifact.metadata.get("data_sources", []):
        md_lines.append(f"- {ds.get('name', ds)}")
    if findings:
        md_lines.extend(["", "## Optimization findings", ""])
        for f in findings:
            md_lines.append(f"- [{f.get('severity', 'info')}] {f.get('message', '')}")
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
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
        for nid in tg.topological_order():
            node = tg.nodes[nid]
            if node.node_kind == "source":
                obj = node.properties.get("object_name", node.node_id)
                lines.append(f"-- SOURCE: {obj}")
            elif node.node_kind == "join":
                jt = node.properties.get("join_type", "inner")
                lines.append(f"-- JOIN ({jt}): {nid}")
            elif node.node_kind == "projection":
                cols = node.properties.get("columns", ["*"])
                lines.append(f"SELECT {', '.join(cols)} FROM {nid};")
    else:
        lines.append(f"SELECT * FROM \"{artifact.schema}\".\"{artifact.name}\";")
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
    md.write_text(
        f"# ABAP Program: {artifact.name}\n\nTables: {', '.join(meta.get('tables', []))}\n",
        encoding="utf-8",
    )
    paths.append(md)
    paths.append(generate_lineage_json(artifact, store, output_dir / "abap" / "lineage" / f"{slug}.json"))
    return paths


def _generate_odata(artifact: CanonicalArtifact, store: ArtifactGraphStore, output_dir: Path) -> list[Path]:
    return [_write_canonical_json(artifact, output_dir)]
