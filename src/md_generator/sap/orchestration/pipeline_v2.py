from __future__ import annotations

import json
import logging
from pathlib import Path

from md_generator.sap.canonical.loader import canonical_from_object
from md_generator.sap.graph.backends.memory import InMemoryGraphStore
from md_generator.sap.chunking.registry_v2 import SemanticChunkRegistryV2
from md_generator.sap.chunking.spec import SemanticChunkSpec
from md_generator.sap.core.run_context import RunContext
from md_generator.sap.generators.registry import default_generator_registry
from md_generator.sap.graph.adapters.networkx import artifact_graph_to_networkx
from md_generator.sap.graph.adapters.openlineage import OpenLineageMapper
from md_generator.sap.graph.store import ArtifactGraphStore
from md_generator.sap.index.metadata_index import MetadataIndex
from md_generator.sap.index.semantic_entity_registry import SemanticEntityRegistry
from md_generator.sap.lineage.cross_system import link_cross_system_lineage
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.normalizer.registry import default_normalizer_registry
from md_generator.sap.orchestration.pipeline import run_pipeline_legacy
from md_generator.sap.rules.engine import DeterministicRuleEngine

logger = logging.getLogger(__name__)


def _refresh_entity_ddic_markdown(ctx: RunContext, unified, store) -> None:
    from md_generator.sap.markdown.builders.entity_builder import build_entity_markdown
    from md_generator.sap.markdown.builders.renderer_context import RendererContext
    from md_generator.sap.markdown.cross_link_registry import build_cross_link_registry
    from md_generator.sap.models.entities.kinds import SapObjectKind

    ddic_kinds = {
        SapObjectKind.DATA_ELEMENT,
        SapObjectKind.DOMAIN,
        SapObjectKind.STRUCTURE,
        SapObjectKind.TABLE,
        SapObjectKind.TABLE_TYPE,
        SapObjectKind.RANGE_TYPE,
        SapObjectKind.REFERENCE_TYPE,
    }
    cross = build_cross_link_registry(
        path_registry=unified.path_registry,
        graph_store=store,
        link_graph=ctx.link_graph,
    )
    render_ctx = RendererContext(
        link_graph=ctx.link_graph,
        path_registry=unified.path_registry,
        cross_link_registry=cross,
    )
    for obj in ctx.objects:
        if obj.kind not in ddic_kinds:
            continue
        rel_path = ctx.link_graph.entity_rel_path(obj.package, obj.name) if ctx.link_graph else None
        if not rel_path:
            continue
        path = ctx.output_dir / rel_path
        if not path.is_file():
            continue
        md = build_entity_markdown(obj, link_graph=ctx.link_graph, renderer_ctx=render_ctx)
        path.write_text(md, encoding="utf-8")


def run_pipeline_v2(ctx: RunContext) -> None:
    """Canonical + ArtifactGraph pipeline; runs v1 markdown first for compatibility."""
    from md_generator.sap.canonical.base import CanonicalArtifact

    run_pipeline_legacy(ctx)

    cfg = ctx.config
    root = ctx.output_dir
    normalizer = default_normalizer_registry()
    store: InMemoryGraphStore = InMemoryGraphStore(graph_id="run")
    registry = SemanticEntityRegistry()
    index = MetadataIndex(root / "index")
    artifacts: list[CanonicalArtifact] = []

    catalog_path = Path(__file__).resolve().parent.parent / "rules" / "catalog.yaml"
    rule_engine = DeterministicRuleEngine(catalog_path if cfg.pipeline.rule_engine else None)
    chunk_registry = SemanticChunkRegistryV2()

    for obj in ctx.objects:
        artifact, fragment = canonical_from_object(obj, normalizer)
        if artifact is None:
            continue
        store.add_fragment(fragment)
        registry.register(artifact.identity)
        index.register(artifact)
        findings = rule_engine.evaluate(artifact, store) if cfg.pipeline.rule_engine else []
        if findings:
            artifact.metadata["rule_findings"] = findings
            for finding in findings:
                chunk_registry.register(
                    SemanticChunkSpec(
                        chunk_id=f"{artifact.identity.stable_id}:finding:{finding.get('rule_id')}",
                        chunk_type="optimization",
                        artifact_type=artifact.artifact_type,
                        artifact_id=artifact.identity.stable_id,
                        semantic_id=artifact.identity.semantic_id or None,
                        section="Optimization findings",
                        semantic_tags=finding.get("semantic_tags", ["performance"]),
                        content=finding.get("message", ""),
                    )
                )
        artifacts.append(artifact)

    if cfg.pipeline.cross_lineage:
        link_cross_system_lineage(store, registry)

    if cfg.pipeline.artifact_graph:
        graph_path = root / "graph" / "artifacts.json"
        graph_path.parent.mkdir(parents=True, exist_ok=True)
        graph_path.write_text(json.dumps(store.to_dict(), indent=2), encoding="utf-8")
        merged = root / "graph-full-v2.json"
        merged.write_text(json.dumps(store.to_dict(), indent=2), encoding="utf-8")
        ctx.graph = artifact_graph_to_networkx(store.graph)

    if cfg.pipeline.canonical_json:
        from md_generator.sap.framework.paths import safe_filename

        for artifact in artifacts:
            fname = safe_filename(artifact.identity.stable_id, ".json")
            path = root / "json" / "canonical" / fname
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(artifact.model_dump(mode="json"), indent=2), encoding="utf-8")

    gen_reg = default_generator_registry()
    if artifacts:
        gen_reg.generate_all(
            artifacts,
            store,
            root,
            semantic_narrative=cfg.pipeline.semantic_narrative,
            link_graph=ctx.link_graph,
        )
        from md_generator.sap.markdown.unified_output_registry import build_unified_output_registry

        unified = build_unified_output_registry(artifacts, ctx.link_graph)
        unified.write_navigation_index(root, run_id=str(int(ctx.started_at.timestamp())))
        _refresh_entity_ddic_markdown(ctx, unified, store)

    if cfg.pipeline.openlineage_export:
        ol = OpenLineageMapper(run_id=str(ctx.started_at.timestamp()))
        ol_path = root / "lineage" / "openlineage.json"
        ol_path.parent.mkdir(parents=True, exist_ok=True)
        ol_path.write_text(json.dumps(ol.to_openlineage(store), indent=2), encoding="utf-8")

    if cfg.chunking.enabled or cfg.pipeline.semantic_chunks_jsonl:
        chunk_registry.write_jsonl(root / "chunks" / "semantic.jsonl")

    index.write()
