from __future__ import annotations

from pathlib import Path

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.transformation.graph import TransformationGraph
from md_generator.sap.canonical.transformation.node import HanaSourceNode
from md_generator.sap.framework.artifact import file_checksum
from md_generator.sap.graph.model import ArtifactGraph, GraphNode
from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.models.metadata.odata import SapObjectCategory
from md_generator.sap.parser.base import SapParseResult
from md_generator.sap.parser.hana.xml_stream import iterparse_events, text


def parse_hana_variant_xml(
    path: Path,
    *,
    artifact_type: str,
    execution_semantic: str,
    xml_hint: str,
    stable_prefix: str,
) -> SapParseResult:
    name = path.stem
    schema = ""
    for tag, elem in iterparse_events(str(path), {xml_hint, "view"}):
        if tag in {xml_hint, "view"}:
            name = text(elem, "name", path.stem) or path.stem
            schema = text(elem, "schema", "")
    return _build_result(path, name, schema, artifact_type, execution_semantic, f"{stable_prefix}::{schema}::{name}")


def parse_hana_variant_text(
    path: Path,
    *,
    artifact_type: str,
    execution_semantic: str,
    stable_prefix: str,
) -> SapParseResult:
    return _build_result(path, path.stem, "", artifact_type, execution_semantic, f"{stable_prefix}::{path.stem}")


def _build_result(
    path: Path,
    name: str,
    schema: str,
    artifact_type: str,
    execution_semantic: str,
    stable_id: str,
) -> SapParseResult:
    from md_generator.sap.canonical.identity import ArtifactIdentity
    from md_generator.sap.canonical.provenance import ProvenanceBundle

    checksum = file_checksum(path)
    stable_id = stable_id.replace(" ", "_")
    tg = TransformationGraph(graph_id=f"tg:{stable_id}", execution_semantic=execution_semantic)
    tg.add_node(HanaSourceNode(node_id=f"src:{name}", object_name=name))
    g = ArtifactGraph(graph_id=f"hana:{stable_id}")
    g.add_node(
        GraphNode(
            node_id=stable_id,
            node_kind="artifact",
            label=name,
            namespace="HANA::",
            artifact_type=artifact_type,
        )
    )
    identity = ArtifactIdentity(
        stable_id=stable_id,
        physical_id=f"{schema}.{name}" if schema else name,
        display_id=name,
        namespace="HANA::",
    )
    provenance = ProvenanceBundle(
        parser_id=f"hana.{artifact_type.split('.')[-1]}",
        parser_version="1.0.0",
        source_checksum=checksum,
    )
    canonical = CanonicalArtifact(
        identity=identity,
        provenance=provenance,
        artifact_type=artifact_type,
        name=name,
        schema=schema,
        source_path=str(path),
        source_system="hana",
        artifact_hash=checksum,
        transformation_graph_id=tg.graph_id,
        graph_fragment_id=g.graph_id,
        metadata={"transformation_graph": tg.model_dump(mode="json")},
    )
    obj = SapObject(
        kind=SapObjectKind.HANA_CALCULATION_VIEW,
        name=name,
        package=schema,
        description=f"HANA {artifact_type}: {name}",
        source_path=path,
        raw_metadata={
            "hana": {"type": artifact_type},
            "canonical": canonical.model_dump(mode="json"),
            "graph_fragment": g.model_dump(mode="json"),
        },
        category=SapObjectCategory.METADATA,
        is_catalog_object=True,
    )
    return SapParseResult(path=path, objects=[obj], metadata={"execution_semantic": execution_semantic})
