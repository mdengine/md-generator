from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from md_generator.sap.framework.artifact import file_checksum
from md_generator.sap.framework.capabilities import ParserCapability
from md_generator.sap.graph.model import ArtifactGraph, GraphEdge, GraphNode
from md_generator.sap.graph.taxonomy import RelationshipType
from md_generator.sap.parser.base import ParseContext, SapParseResult


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _bw_capabilities(*, sql: str = "no") -> ParserCapability:
    return ParserCapability(
        lineage=True,
        sql_generation=sql,  # type: ignore[arg-type]
        impact_analysis=True,
        semantic_id=True,
        transformation_graph=True,
    )


def _emit_bw_result(
    path: Path,
    *,
    kind: object,
    artifact_type: str,
    name: str,
    package: str,
    namespace: str,
    canonical_model: type,
    canonical_data: dict[str, Any],
    graph: ArtifactGraph,
    execution_semantic: str,
) -> SapParseResult:
    from md_generator.sap.models.entities.sap_object import SapObject
    from md_generator.sap.models.metadata.odata import SapObjectCategory

    artifact = canonical_model.model_validate(canonical_data)
    obj = SapObject(
        kind=kind,
        name=name,
        package=package,
        description=f"BW {artifact_type}: {name}",
        source_path=path,
        raw_metadata={
            "bw": {"type": artifact_type},
            "canonical": canonical_data,
            "graph_fragment": graph.model_dump(mode="json"),
        },
        category=SapObjectCategory.METADATA,
        is_catalog_object=True,
    )
    return SapParseResult(
        path=path,
        objects=[obj],
        metadata={"graph_fragment": graph.model_dump(mode="json"), "execution_semantic": execution_semantic},
    )


def _base_graph(stable_id: str, name: str, namespace: str, artifact_type: str) -> ArtifactGraph:
    g = ArtifactGraph(graph_id=f"bw:{stable_id}")
    g.add_node(
        GraphNode(
            node_id=stable_id,
            node_kind="artifact",
            label=name,
            namespace=namespace,
            artifact_type=artifact_type,
        )
    )
    return g


def _identity(stable_id: str, name: str, namespace: str, package: str = "BW"):
    from md_generator.sap.canonical.identity import ArtifactIdentity

    return ArtifactIdentity(
        stable_id=stable_id,
        physical_id=name,
        display_id=name,
        namespace=namespace,
        semantic_id=f"entity:{name.lower()}",
    )


def _provenance(path: Path, parser_id: str) -> object:
    from md_generator.sap.canonical.provenance import ProvenanceBundle

    checksum = file_checksum(path)
    return ProvenanceBundle(
        parser_id=parser_id,
        parser_version="1.0.0",
        source_checksum=checksum,
        artifact_version=checksum[:16],
    )


def _add_reads(g: ArtifactGraph, src: str, target: str, target_label: str) -> None:
    tid = f"BW::{target}"
    g.add_node(GraphNode(node_id=tid, node_kind="dataset", label=target_label, namespace="BW::"))
    g.add_edge(
        GraphEdge(
            edge_id=f"{src}->reads->{tid}",
            source_id=src,
            target_id=tid,
            relationship=RelationshipType.READS_FROM,
        )
    )


def _tg(graph_id: str, execution_semantic: str, nodes: list) -> object:
    from md_generator.sap.canonical.transformation.graph import TransformationGraph

    tg = TransformationGraph(graph_id=graph_id, execution_semantic=execution_semantic)
    for n in nodes:
        tg.add_node(n)
    return tg
