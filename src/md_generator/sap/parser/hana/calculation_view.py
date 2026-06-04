from __future__ import annotations

import hashlib
from pathlib import Path

from md_generator.sap.canonical.hana.calculation_view import (
    Attribute,
    CalculationView,
    CalculatedColumn,
    DataSource,
    Measure,
)
from md_generator.sap.canonical.identity import ArtifactIdentity
from md_generator.sap.canonical.provenance import ProvenanceBundle
from md_generator.sap.canonical.transformation.graph import TransformationGraph
from md_generator.sap.canonical.transformation.node import (
    HanaJoinNode,
    HanaProjectionNode,
    HanaSourceNode,
    JoinCondition,
)
from md_generator.sap.framework.artifact import file_checksum
from md_generator.sap.graph.model import ArtifactGraph, GraphEdge, GraphNode
from md_generator.sap.graph.taxonomy import RelationshipType
from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.models.metadata.odata import SapObjectCategory
from md_generator.sap.framework.capabilities import ParserCapability
from md_generator.sap.parser.base import ParseContext, SapParseResult, SapParserPlugin
from md_generator.sap.parser.hana.xml_stream import iterparse_events, local_tag, text


class HanaCalculationViewParser(SapParserPlugin):
    name = "hana.calculation_view"
    version = "1.0.0"

    def capabilities(self) -> ParserCapability:
        return ParserCapability(
            lineage=True,
            sql_generation="yes",
            impact_analysis=True,
            semantic_id=True,
            transformation_graph=True,
        )

    def can_parse(self, path: Path) -> bool:
        if path.suffix.lower() not in (".xml", ".calculationview"):
            return False
        from md_generator.sap.parser.odata.parser import _is_odata_metadata

        if _is_odata_metadata(path):
            return False
        try:
            head = path.read_text(encoding="utf-8", errors="ignore")[:4096]
        except OSError:
            return False
        head_lower = head.lower()
        return "calculation:scenario" in head_lower or "<calculationscenario" in head_lower

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult | None:
        cv, graph_frag = parse_calculation_view_xml(path)
        obj = SapObject(
            kind=SapObjectKind.HANA_CALCULATION_VIEW,
            name=cv.name,
            package=cv.package,
            description=f"HANA Calculation View {cv.name}",
            source_path=path,
            raw_metadata={"hana": cv.to_metadata_dict(), "canonical": cv.model_dump(mode="json"), "graph_fragment": graph_frag.model_dump(mode="json")},
            semantic_entity=cv.identity.semantic_id or None,
            category=SapObjectCategory.METADATA,
            is_catalog_object=True,
        )
        return SapParseResult(
            path=path,
            objects=[obj],
            metadata={"graph_fragment": graph_frag.model_dump(mode="json")},
        )


def parse_calculation_view_xml(path: Path) -> tuple[CalculationView, ArtifactGraph]:
    checksum = file_checksum(path)
    name = path.stem
    schema = ""
    package = ""
    data_sources: list[DataSource] = []
    attributes: list[Attribute] = []
    measures: list[Measure] = []
    calculated: list[CalculatedColumn] = []
    tg = TransformationGraph(graph_id=f"tg:{path.stem}", execution_semantic="hana_cv")
    graph = ArtifactGraph(graph_id=f"hana:{path.stem}")
    stable_id = f"HANA::{schema or '_'}::{name}".replace(" ", "_")

    for tag, elem in iterparse_events(str(path), {"calculationScenario", "dataSource", "join", "projectionView"}):
        if tag == "calculationScenario":
            name = text(elem, "name", path.stem) or path.stem
            schema = text(elem, "schema", "")
            package = text(elem, "package", "")
            stable_id = f"HANA::{schema}::{name}".replace(" ", "_")
        elif tag == "dataSource":
            ds_name = text(elem, "id") or text(elem, "name")
            ds_schema = text(elem, "schema")
            ds_type = text(elem, "type", "table")
            data_sources.append(DataSource(name=ds_name, schema=ds_schema, object_type=ds_type))
            src_id = f"{ds_schema}.{ds_name}" if ds_schema else ds_name
            node_id = f"src:{src_id}"
            tg.add_node(HanaSourceNode(node_id=node_id, object_name=src_id, outputs=[f"after:{node_id}"]))
            ds_node = f"DS::{src_id}"
            graph.add_node(GraphNode(node_id=ds_node, node_kind="dataset", label=src_id, namespace="HANA::"))
            graph.add_edge(
                GraphEdge(
                    edge_id=f"{stable_id}->reads->{ds_node}",
                    source_id=stable_id,
                    target_id=ds_node,
                    relationship=RelationshipType.READS_FROM,
                )
            )
        elif tag == "join":
            join_id = text(elem, "id", f"join_{len(tg.nodes)}")
            join_type = text(elem, "joinType", "inner")
            conditions: list[JoinCondition] = []
            for child in elem:
                if local_tag(child) == "condition":
                    conditions.append(
                        JoinCondition(
                            left=text(child, "left"),
                            right=text(child, "right"),
                            operator=text(child, "operator", "="),
                        )
                    )
            inputs = [text(elem, "leftInput"), text(elem, "rightInput")]
            inputs = [i for i in inputs if i]
            tg.add_node(
                HanaJoinNode(
                    node_id=join_id,
                    join_type=join_type,
                    conditions=conditions,
                    inputs=inputs,
                    outputs=[f"out:{join_id}"],
                    properties={"join_type": join_type},
                )
            )
            graph.add_edge(
                GraphEdge(
                    edge_id=f"{stable_id}->joins->{join_id}",
                    source_id=stable_id,
                    target_id=join_id,
                    relationship=RelationshipType.JOINS,
                    properties={"join_type": join_type},
                )
            )
        elif tag == "projectionView":
            proj_id = text(elem, "id", f"proj_{len(tg.nodes)}")
            cols: list[str] = []
            for child in elem:
                if local_tag(child) == "viewAttribute":
                    cols.append(text(child, "id") or text(child, "name"))
            tg.add_node(
                HanaProjectionNode(
                    node_id=proj_id,
                    inputs=[text(elem, "input")],
                    outputs=[f"out:{proj_id}"],
                    properties={"columns": cols or ["*"]},
                )
            )
            for col in cols:
                graph.add_edge(
                    GraphEdge(
                        edge_id=f"{proj_id}->derives->{col}",
                        source_id=proj_id,
                        target_id=f"{stable_id}::{col}",
                        relationship=RelationshipType.DERIVES_FROM,
                        properties={"column": col},
                    )
                )

    for child_path in _scan_attributes_measures(path):
        pass  # attributes/measures filled via secondary scan below

    _fill_attributes_measures(path, attributes, measures, calculated)

    identity = ArtifactIdentity(
        stable_id=stable_id,
        physical_id=f"{schema}.{name}" if schema else name,
        display_id=name,
        namespace="HANA::",
    )
    provenance = ProvenanceBundle(
        parser_id="hana.calculation_view",
        parser_version="1.0.0",
        source_checksum=checksum,
        artifact_version=checksum[:16],
    )
    graph.add_node(
        GraphNode(
            node_id=stable_id,
            node_kind="artifact",
            label=name,
            namespace="HANA::",
            artifact_type="hana.calculation_view",
            properties={"schema": schema, "package": package},
        )
    )
    cv = CalculationView(
        identity=identity,
        provenance=provenance,
        name=name,
        schema=schema,
        package=package,
        source_path=str(path),
        source_system="hana",
        data_sources=data_sources,
        transformation_graph=tg,
        calculated_columns=calculated,
        attributes=attributes,
        measures=measures,
        artifact_hash=checksum,
        graph_fragment_id=graph.graph_id,
        transformation_graph_id=tg.graph_id,
        metadata={
            "data_sources": [ds.model_dump(mode="json") for ds in data_sources],
            "transformation_graph": tg.model_dump(mode="json"),
        },
    )
    return cv, graph


def _scan_attributes_measures(path: Path) -> list[str]:
    return []


def _fill_attributes_measures(
    path: Path,
    attributes: list[Attribute],
    measures: list[Measure],
    calculated: list[CalculatedColumn],
) -> None:
    try:
        for tag, elem in iterparse_events(str(path), {"viewAttribute", "measure", "calculatedViewAttribute"}):
            if tag == "viewAttribute":
                attributes.append(Attribute(name=text(elem, "id") or text(elem, "name"), data_type=text(elem, "datatype")))
            elif tag == "measure":
                measures.append(Measure(name=text(elem, "id") or text(elem, "name"), aggregation=text(elem, "aggregation")))
            elif tag == "calculatedViewAttribute":
                calculated.append(
                    CalculatedColumn(
                        name=text(elem, "id") or text(elem, "name"),
                        expression=text(elem, "formula") or text(elem, "expression"),
                    )
                )
    except ImportError:
        pass


class HanaCalculationViewParserPlugin(HanaCalculationViewParser):
    pass
