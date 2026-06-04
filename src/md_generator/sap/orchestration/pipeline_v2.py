from __future__ import annotations

import json
import logging
from pathlib import Path

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.hana.calculation_view import CalculationView
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


def _canonical_from_object(obj: SapObject, normalizer) -> tuple[CanonicalArtifact | None, object]:
    if obj.raw_metadata and "hana" in obj.raw_metadata and "canonical" in obj.raw_metadata:
        data = obj.raw_metadata["canonical"]
        try:
            cv = CalculationView.model_validate(data)
            frag_data = obj.raw_metadata.get("graph_fragment")
            from md_generator.sap.graph.model import ArtifactGraph

            frag = ArtifactGraph.model_validate(frag_data) if frag_data else ArtifactGraph(graph_id=cv.identity.stable_id)
            return cv, frag
        except Exception as e:
            logger.warning("Failed to load HANA canonical for %s: %s", obj.name, e)
    return normalizer.normalize(obj)


def run_pipeline_v2(ctx: RunContext) -> None:
    """Canonical + ArtifactGraph pipeline; runs v1 markdown first for compatibility."""
    run_pipeline_legacy(ctx)

    cfg = ctx.config
    root = ctx.output_dir
    normalizer = default_normalizer_registry()
    store = ArtifactGraphStore(graph_id="run")
    registry = SemanticEntityRegistry()
    index = MetadataIndex(root / "index")
    artifacts: list[CanonicalArtifact] = []

    catalog_path = Path(__file__).resolve().parent.parent / "rules" / "catalog.yaml"
    rule_engine = DeterministicRuleEngine(catalog_path if cfg.pipeline.rule_engine else None)
    chunk_registry = SemanticChunkRegistryV2()

    for obj in ctx.objects:
        artifact, fragment = _canonical_from_object(obj, normalizer)
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
        gen_reg.generate_all(artifacts, store, root)

    if cfg.pipeline.openlineage_export:
        ol = OpenLineageMapper(run_id=str(ctx.started_at.timestamp()))
        ol_path = root / "lineage" / "openlineage.json"
        ol_path.parent.mkdir(parents=True, exist_ok=True)
        ol_path.write_text(json.dumps(ol.to_openlineage(store), indent=2), encoding="utf-8")

    if cfg.chunking.enabled or cfg.pipeline.semantic_chunks_jsonl:
        chunk_registry.write_jsonl(root / "chunks" / "semantic.jsonl")

    index.write()
