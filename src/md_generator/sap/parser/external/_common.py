from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.framework.artifact import file_checksum
from md_generator.sap.framework.capabilities import ParserCapability
from md_generator.sap.graph.model import ArtifactGraph, GraphNode
from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.models.metadata.odata import SapObjectCategory
from md_generator.sap.parser.base import SapParseResult


def _ext_capabilities(*, sql: str = "partial") -> ParserCapability:
    return ParserCapability(
        lineage=True,
        sql_generation=sql,  # type: ignore[arg-type]
        impact_analysis=True,
        semantic_id=True,
        transformation_graph=False,
    )


def _emit_external(
    path: Path,
    *,
    artifact_type: str,
    namespace: str,
    name: str,
    parser_id: str,
    metadata: dict[str, Any],
) -> SapParseResult:
    from md_generator.sap.canonical.identity import ArtifactIdentity
    from md_generator.sap.canonical.provenance import ProvenanceBundle

    checksum = file_checksum(path)
    stable_id = f"{namespace}{name}".replace(" ", "_")
    identity = ArtifactIdentity(
        stable_id=stable_id,
        physical_id=name,
        display_id=name,
        namespace=namespace,
        semantic_id=f"entity:{name.lower()}",
    )
    provenance = ProvenanceBundle(
        parser_id=parser_id,
        parser_version="1.0.0",
        source_checksum=checksum,
    )
    canonical = CanonicalArtifact(
        identity=identity,
        provenance=provenance,
        artifact_type=artifact_type,
        name=name,
        source_path=str(path),
        source_system="external",
        artifact_hash=checksum,
        metadata=metadata,
    )
    g = ArtifactGraph(graph_id=f"ext:{stable_id}")
    g.add_node(
        GraphNode(
            node_id=stable_id,
            node_kind="artifact",
            label=name,
            namespace=namespace,
            artifact_type=artifact_type,
        )
    )
    obj = SapObject(
        kind=SapObjectKind.UNKNOWN,
        name=name,
        package=namespace.rstrip(":"),
        description=f"External {artifact_type}: {name}",
        source_path=path,
        raw_metadata={
            "external": metadata,
            "canonical": canonical.model_dump(mode="json"),
            "graph_fragment": g.model_dump(mode="json"),
        },
        category=SapObjectCategory.METADATA,
    )
    return SapParseResult(path=path, objects=[obj])
