from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from md_generator.sap.framework.artifact import file_checksum
from md_generator.sap.framework.capabilities import ParserCapability
from md_generator.sap.graph.model import ArtifactGraph, GraphEdge, GraphNode
from md_generator.sap.graph.taxonomy import RelationshipType


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _ds_capabilities() -> ParserCapability:
    return ParserCapability(
        lineage=True,
        sql_generation="partial",
        impact_analysis=True,
        semantic_id=True,
        transformation_graph=True,
    )


def _identity(stable_id: str, name: str) -> object:
    from md_generator.sap.canonical.identity import ArtifactIdentity

    return ArtifactIdentity(
        stable_id=stable_id,
        physical_id=name,
        display_id=name,
        namespace="DATASPHERE::",
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


def _emit(path: Path, *, kind, artifact_type: str, name: str, model, data: dict, graph: ArtifactGraph, sem: str):
    from md_generator.sap.models.entities.sap_object import SapObject
    from md_generator.sap.models.metadata.odata import SapObjectCategory
    from md_generator.sap.parser.base import SapParseResult

    artifact = model.model_validate(data)
    obj = SapObject(
        kind=kind,
        name=name,
        package=data.get("package", "DATASPHERE"),
        description=f"Datasphere {artifact_type}: {name}",
        source_path=path,
        raw_metadata={
            "datasphere": {"type": artifact_type},
            "canonical": data,
            "graph_fragment": graph.model_dump(mode="json"),
        },
        category=SapObjectCategory.METADATA,
        is_catalog_object=True,
    )
    return SapParseResult(path=path, objects=[obj], metadata={"execution_semantic": sem})


def _graph(stable_id: str, name: str, artifact_type: str) -> ArtifactGraph:
    g = ArtifactGraph(graph_id=f"ds:{stable_id}")
    g.add_node(
        GraphNode(
            node_id=stable_id,
            node_kind="artifact",
            label=name,
            namespace="DATASPHERE::",
            artifact_type=artifact_type,
        )
    )
    return g


def _tg(gid: str, sem: str, nodes: list) -> object:
    from md_generator.sap.canonical.transformation.graph import TransformationGraph

    tg = TransformationGraph(graph_id=gid, execution_semantic=sem)
    for n in nodes:
        tg.add_node(n)
    return tg
