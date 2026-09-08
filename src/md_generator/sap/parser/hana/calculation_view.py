from __future__ import annotations

from pathlib import Path

from md_generator.sap.canonical.hana.calculation_view import (
    Attribute,
    CalculationView,
    CalculatedColumn,
    DataSource,
    InputParameter,
    Measure,
    Variable,
)
from md_generator.sap.canonical.identity import ArtifactIdentity
from md_generator.sap.canonical.provenance import ProvenanceBundle
from md_generator.sap.canonical.transformation.graph import TransformationGraph
from md_generator.sap.canonical.transformation.node import (
    HanaAggregateNode,
    HanaFilterNode,
    HanaJoinNode,
    HanaProjectionNode,
    HanaSourceNode,
    JoinCondition,
)
from md_generator.sap.framework.artifact import file_checksum
from md_generator.sap.framework.capabilities import ParserCapability
from md_generator.sap.graph.model import ArtifactGraph, GraphEdge, GraphNode
from md_generator.sap.graph.taxonomy import RelationshipType
from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.models.metadata.odata import SapObjectCategory
from md_generator.sap.parser.base import ParseContext, SapParseResult, SapParserPlugin
from md_generator.sap.parser.hana.xml_stream import iterparse_events, local_tag, text

_PARSE_TAGS = {
    "scenario",
    "calculationScenario",
    "DataSource",
    "dataSource",
    "calculationView",
    "projectionView",
    "join",
    "variable",
    "attribute",
}


class HanaCalculationViewParser(SapParserPlugin):
    name = "hana.calculation_view"
    version = "1.1.0"

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
            description=cv.semantics.get("description") or f"HANA Calculation View {cv.name}",
            source_path=path,
            raw_metadata={
                "hana": cv.to_metadata_dict(),
                "canonical": cv.model_dump(mode="json"),
                "graph_fragment": graph_frag.model_dump(mode="json"),
            },
            semantic_entity=cv.identity.semantic_id or None,
            category=SapObjectCategory.METADATA,
            is_catalog_object=True,
        )
        return SapParseResult(
            path=path,
            objects=[obj],
            metadata={"graph_fragment": graph_frag.model_dump(mode="json")},
        )


def _attr(elem: object, key: str, default: str = "") -> str:
    val = getattr(elem, "get", lambda _k, _d=None: None)(key)
    if val is not None:
        return str(val).strip()
    return default


def _child_attr(elem: object, child: str, attr: str, default: str = "") -> str:
    for c in elem:
        if local_tag(c) == child:
            return _attr(c, attr, default)
    return default


def _description(elem: object) -> str:
    for c in elem:
        if local_tag(c) == "descriptions":
            return _attr(c, "defaultDescription") or (c.text or "").strip()
    return ""


def _parse_path_identity(path: Path, scenario_id: str) -> tuple[str, str]:
    stem = path.stem
    lower = stem.lower()
    if lower.endswith(".calculationview"):
        stem = stem[: -len(".calculationview")]
    package = ""
    if "#" in stem:
        package, file_view = stem.split("#", 1)
        name = scenario_id or file_view
    else:
        name = scenario_id or stem
    return name, package


def _calc_view_type(elem: object) -> str:
    xsi_type = _attr(elem, "{http://www.w3.org/2001/XMLSchema-instance}type")
    if not xsi_type:
        xsi_type = _attr(elem, "type")
    if "JoinView" in xsi_type:
        return "join"
    if "AggregationView" in xsi_type:
        return "aggregate"
    if "ProjectionView" in xsi_type:
        return "projection"
    if local_tag(elem) == "join":
        return "join"
    if local_tag(elem) == "projectionView":
        return "projection"
    return "projection"


def _calc_view_inputs(elem: object) -> list[str]:
    inputs: list[str] = []
    for child in elem:
        tag = local_tag(child)
        if tag == "input":
            node = _attr(child, "node") or text(child, "node")
            if node.startswith("#"):
                node = node[1:]
            if node:
                inputs.append(node)
        elif tag in ("leftInput", "rightInput"):
            val = (child.text or "").strip()
            if val:
                inputs.append(val)
    single = text(elem, "input")
    if single:
        if single.startswith("#"):
            single = single[1:]
        if single and single not in inputs:
            inputs.append(single)
    return inputs


def _calc_view_columns(elem: object) -> list[str]:
    cols: list[str] = []
    for child in elem:
        if local_tag(child) == "viewAttributes":
            for va in child:
                if local_tag(va) == "viewAttribute":
                    col = _attr(va, "id") or _attr(va, "name")
                    if col:
                        cols.append(col)
        elif local_tag(child) == "viewAttribute":
            col = _attr(child, "id") or _attr(child, "name")
            if col:
                cols.append(col)
    return cols


def _calc_view_filter(elem: object) -> str:
    for child in elem:
        if local_tag(child) == "filter":
            return (child.text or "").strip()
    return ""


def _calc_view_join_keys(elem: object) -> list[str]:
    keys: list[str] = []
    for child in elem:
        if local_tag(child) == "joinAttribute":
            key = _attr(child, "name")
            if key:
                keys.append(key)
    return keys


def _calc_view_calculated(elem: object) -> list[CalculatedColumn]:
    cols: list[CalculatedColumn] = []
    for child in elem:
        if local_tag(child) == "calculatedViewAttributes":
            for calc in child:
                if local_tag(calc) == "calculatedViewAttribute":
                    cname = _attr(calc, "id") or _attr(calc, "name")
                    if cname:
                        cols.append(
                            CalculatedColumn(
                                name=cname,
                                expression=text(calc, "formula") or text(calc, "expression"),
                                data_type=_attr(calc, "datatype"),
                            )
                        )
    return cols


def _fill_attributes_measures(
    path: Path,
    attributes: list[Attribute],
    measures: list[Measure],
    calculated: list[CalculatedColumn],
    attribute_names: set[str],
    measure_names: set[str],
    calculated_names: set[str],
) -> None:
    try:
        for tag, elem in iterparse_events(
            str(path),
            {"viewAttribute", "measure", "calculatedViewAttribute"},
        ):
            if tag == "viewAttribute":
                col = _attr(elem, "id") or _attr(elem, "name")
                if col and col not in attribute_names:
                    attributes.append(Attribute(name=col, data_type=_attr(elem, "datatype")))
                    attribute_names.add(col)
            elif tag == "measure":
                mname = _attr(elem, "id") or _attr(elem, "name")
                if mname and mname not in measure_names:
                    measures.append(Measure(name=mname, aggregation=_attr(elem, "aggregation")))
                    measure_names.add(mname)
            elif tag == "calculatedViewAttribute":
                cname = _attr(elem, "id") or _attr(elem, "name")
                if cname and cname not in calculated_names:
                    calculated.append(
                        CalculatedColumn(
                            name=cname,
                            expression=text(elem, "formula") or text(elem, "expression"),
                            data_type=_attr(elem, "datatype"),
                        )
                    )
                    calculated_names.add(cname)
    except ImportError:
        pass


def _parse_data_source(elem: object, tag: str) -> DataSource:
    ds_id = _attr(elem, "id") or text(elem, "id") or text(elem, "name")
    ds_type = _attr(elem, "type", "table")
    schema = text(elem, "schema") or _child_attr(elem, "columnObject", "schemaName")
    name = text(elem, "name") or _child_attr(elem, "columnObject", "columnObjectName") or ds_id
    if not schema and tag == "dataSource":
        schema = text(elem, "schema")
    return DataSource(name=name or ds_id, db_schema=schema, object_type=ds_type)


def _link_graph_nodes(
    tg: TransformationGraph,
    graph: ArtifactGraph,
    stable_id: str,
    node_id: str,
    inputs: list[str],
    data_source_keys: set[str],
    calc_view_keys: set[str],
) -> None:
    for inp in inputs:
        if inp in data_source_keys:
            src_node = f"src:{inp}"
            if src_node in tg.nodes:
                outs = list(tg.nodes[src_node].outputs)
                if node_id not in outs:
                    outs.append(node_id)
                    tg.nodes[src_node].outputs = outs
        elif inp in calc_view_keys and inp in tg.nodes:
            outs = list(tg.nodes[inp].outputs)
            if node_id not in outs:
                outs.append(node_id)
                tg.nodes[inp].outputs = outs


def parse_calculation_view_xml(path: Path) -> tuple[CalculationView, ArtifactGraph]:
    checksum = file_checksum(path)
    name = path.stem
    schema = ""
    package = ""
    description = ""
    data_category = ""
    scenario_type = ""
    data_sources: list[DataSource] = []
    data_source_keys: set[str] = set()
    attributes: list[Attribute] = []
    attribute_names: set[str] = set()
    measures: list[Measure] = []
    measure_names: set[str] = set()
    calculated: list[CalculatedColumn] = []
    calculated_names: set[str] = set()
    variables: list[Variable] = []
    variable_names: set[str] = set()
    input_parameters: list[InputParameter] = []
    logical_attributes: list[dict[str, str]] = []
    logical_names: set[str] = set()
    calculation_steps: list[dict[str, object]] = []
    calc_view_keys: set[str] = set()

    tg = TransformationGraph(graph_id=f"tg:{path.stem}", execution_semantic="hana_cv")
    graph = ArtifactGraph(graph_id=f"hana:{path.stem}")
    name, package = _parse_path_identity(path, "")
    stable_id = f"HANA::_::{package or '_'}::{name}".replace(" ", "_")
    pending_reads: list[tuple[str, str]] = []
    pending_joins: list[tuple[str, str, dict[str, object]]] = []
    pending_derives: list[tuple[str, str]] = []

    for tag, elem in iterparse_events(str(path), _PARSE_TAGS):
        if tag in ("scenario", "calculationScenario"):
            if tag == "scenario":
                name = _attr(elem, "id") or name
                data_category = _attr(elem, "dataCategory")
                scenario_type = _attr(elem, "calculationScenarioType")
                description = _description(elem) or description
                schema = schema or _attr(elem, "schema")
                package = package or _attr(elem, "package")
            else:
                name = text(elem, "name") or _attr(elem, "name") or name
                schema = text(elem, "schema") or _attr(elem, "schema") or schema
                package = text(elem, "package") or _attr(elem, "package") or package
            parsed_name, parsed_pkg = _parse_path_identity(path, name)
            name = parsed_name
            package = package or parsed_pkg
            if not schema and data_sources:
                schema = data_sources[0].db_schema
            stable_id = f"HANA::{schema or '_'}::{package or '_'}::{name}".replace(" ", "_")

        elif tag in ("DataSource", "dataSource"):
            ds = _parse_data_source(elem, tag)
            key = _attr(elem, "id") or ds.name
            if key and key not in data_source_keys:
                data_sources.append(ds)
                data_source_keys.add(key)
                if not schema and ds.db_schema:
                    schema = ds.db_schema
                src_id = f"{ds.db_schema}.{ds.name}" if ds.db_schema else ds.name
                node_id = f"src:{key}"
                tg.add_node(
                    HanaSourceNode(
                        node_id=node_id,
                        object_name=src_id,
                        outputs=[],
                        properties={"object_name": src_id, "source_id": key, "object_type": ds.object_type},
                    )
                )
                ds_node = f"DS::{src_id}"
                graph.add_node(GraphNode(node_id=ds_node, node_kind="dataset", label=src_id, namespace="HANA::"))
                pending_reads.append((ds_node, ds_node))

        elif tag in ("calculationView", "projectionView", "join"):
            view_id = _attr(elem, "id") or text(elem, "id") or f"step_{len(calculation_steps)}"
            view_kind = _calc_view_type(elem)
            join_type = _attr(elem, "joinType", "inner")
            inputs = _calc_view_inputs(elem)
            cols = _calc_view_columns(elem)
            filt = _calc_view_filter(elem)
            join_keys = _calc_view_join_keys(elem)
            calc_view_keys.add(view_id)

            step: dict[str, object] = {
                "id": view_id,
                "kind": view_kind,
                "inputs": inputs,
                "columns": cols,
            }
            if view_kind == "join":
                step["join_type"] = join_type
                if join_keys:
                    step["join_keys"] = join_keys
            if filt:
                step["filter"] = filt
            calculation_steps.append(step)

            if view_kind == "join":
                conditions = [JoinCondition(left=k, right=k, operator="=") for k in join_keys]
                tg.add_node(
                    HanaJoinNode(
                        node_id=view_id,
                        join_type=join_type,
                        conditions=conditions,
                        inputs=inputs,
                        outputs=[],
                        properties={"join_type": join_type, "join_keys": join_keys, "columns": cols},
                    )
                )
            elif view_kind == "aggregate":
                tg.add_node(
                    HanaAggregateNode(
                        node_id=view_id,
                        inputs=inputs,
                        outputs=[],
                        properties={"columns": cols or ["*"]},
                    )
                )
            else:
                tg.add_node(
                    HanaProjectionNode(
                        node_id=view_id,
                        inputs=inputs,
                        outputs=[],
                        properties={"columns": cols or ["*"], "filter": filt},
                    )
                )
                if filt:
                    filter_id = f"{view_id}__filter"
                    tg.add_node(
                        HanaFilterNode(
                            node_id=filter_id,
                            inputs=[view_id],
                            outputs=[],
                            expression=filt,
                            properties={"expression": filt},
                        )
                    )
                    tg.nodes[view_id].outputs = [filter_id]

            _link_graph_nodes(tg, graph, stable_id, view_id, inputs, data_source_keys, calc_view_keys)

            if view_kind == "join":
                pending_joins.append(
                    (
                        view_id,
                        join_type,
                        {"join_type": join_type, "join_keys": join_keys},
                    )
                )
            for col in cols:
                pending_derives.append((view_id, col))
            for calc_col in _calc_view_calculated(elem):
                if calc_col.name not in calculated_names:
                    calculated.append(calc_col)
                    calculated_names.add(calc_col.name)

        elif tag == "variable":
            var_id = _attr(elem, "id") or text(elem, "id")
            if not var_id or var_id in variable_names:
                continue
            var_desc = _description(elem)
            datatype = _child_attr(elem, "variableProperties", "datatype")
            mandatory = _child_attr(elem, "variableProperties", "mandatory")
            variables.append(Variable(name=var_id, default_value=var_desc))
            variable_names.add(var_id)
            if _attr(elem, "parameter", "").lower() == "true":
                input_parameters.append(InputParameter(name=var_id, data_type=datatype or mandatory))

        elif tag == "attribute":
            parent = getattr(elem, "getparent", lambda: None)()
            if parent is None or local_tag(parent) != "attributes":
                continue
            grand = getattr(parent, "getparent", lambda: None)()
            if grand is None or local_tag(grand) != "logicalModel":
                continue
            attr_id = _attr(elem, "id")
            if not attr_id or attr_id in logical_names:
                continue
            logical_attributes.append(
                {
                    "name": attr_id,
                    "description": _description(elem),
                    "order": _attr(elem, "order"),
                }
            )
            logical_names.add(attr_id)
            if attr_id not in attribute_names:
                attributes.append(Attribute(name=attr_id, data_type=""))
                attribute_names.add(attr_id)

    _fill_attributes_measures(path, attributes, measures, calculated, attribute_names, measure_names, calculated_names)

    if not schema and data_sources:
        schema = next((ds.db_schema for ds in data_sources if ds.db_schema), "")

    parsed_name, parsed_pkg = _parse_path_identity(path, name)
    name = parsed_name
    package = package or parsed_pkg
    stable_id = f"HANA::{schema or '_'}::{package or '_'}::{name}".replace(" ", "_")

    for ds_node, _ in pending_reads:
        graph.add_edge(
            GraphEdge(
                edge_id=f"{stable_id}->reads->{ds_node}",
                source_id=stable_id,
                target_id=ds_node,
                relationship=RelationshipType.READS_FROM,
            )
        )
    for view_id, join_type, props in pending_joins:
        graph.add_edge(
            GraphEdge(
                edge_id=f"{stable_id}->joins->{view_id}",
                source_id=stable_id,
                target_id=view_id,
                relationship=RelationshipType.JOINS,
                properties=props,
            )
        )
    for view_id, col in pending_derives:
        graph.add_edge(
            GraphEdge(
                edge_id=f"{view_id}->derives->{col}",
                source_id=view_id,
                target_id=f"{stable_id}::{col}",
                relationship=RelationshipType.DERIVES_FROM,
                properties={"column": col},
            )
        )

    if calculation_steps:
        tg.root_node_id = str(calculation_steps[-1].get("id", ""))

    identity = ArtifactIdentity(
        stable_id=stable_id,
        physical_id=f"{package}#{name}" if package else name,
        display_id=name,
        namespace="HANA::",
        semantic_id=f"{schema}.{name}" if schema else name,
    )
    provenance = ProvenanceBundle(
        parser_id="hana.calculation_view",
        parser_version="1.1.0",
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
            properties={"schema": schema, "package": package, "description": description},
        )
    )

    semantics = {
        "description": description,
        "data_category": data_category,
        "scenario_type": scenario_type,
    }

    cv = CalculationView(
        identity=identity,
        provenance=provenance,
        name=name,
        artifact_schema=schema,
        package=package,
        source_path=str(path),
        source_system="hana",
        data_sources=data_sources,
        transformation_graph=tg,
        calculated_columns=calculated,
        attributes=attributes,
        measures=measures,
        variables=variables,
        input_parameters=input_parameters,
        semantics=semantics,
        artifact_hash=checksum,
        graph_fragment_id=graph.graph_id,
        transformation_graph_id=tg.graph_id,
        metadata={
            "data_sources": [ds.model_dump(mode="json") for ds in data_sources],
            "transformation_graph": tg.model_dump(mode="json"),
            "calculated_columns": [c.model_dump(mode="json") for c in calculated],
            "attributes": [a.model_dump(mode="json") for a in attributes],
            "measures": [m.model_dump(mode="json") for m in measures],
            "variables": [v.model_dump(mode="json") for v in variables],
            "input_parameters": [p.model_dump(mode="json") for p in input_parameters],
            "logical_attributes": logical_attributes,
            "calculation_views": calculation_steps,
            "semantics": semantics,
        },
    )
    return cv, graph


class HanaCalculationViewParserPlugin(HanaCalculationViewParser):
    pass
