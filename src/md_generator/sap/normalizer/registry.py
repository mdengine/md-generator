from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.identity import ArtifactIdentity
from md_generator.sap.canonical.provenance import ProvenanceBundle
from md_generator.sap.graph.model import ArtifactGraph, GraphEdge, GraphNode
from md_generator.sap.graph.taxonomy import RelationshipType
from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject


def _base_provenance(obj: SapObject, parser_id: str, parser_version: str) -> ProvenanceBundle:
    return ProvenanceBundle(
        parser_id=parser_id,
        parser_version=parser_version,
        artifact_version=str(obj.source_path or obj.name),
    )


def _identity_for(obj: SapObject, namespace: str) -> ArtifactIdentity:
    return ArtifactIdentity.from_legacy(
        stable_id=obj.object_id,
        name=obj.name,
        namespace=namespace,
        semantic_entity=obj.semantic_entity,
    )


class NormalizerRegistry:
    def __init__(self) -> None:
        self._normalizers: dict[SapObjectKind, Any] = {}

    def register(self, kind: SapObjectKind, fn: Any) -> None:
        self._normalizers[kind] = fn

    def normalize(self, obj: SapObject) -> tuple[CanonicalArtifact | None, ArtifactGraph]:
        fn = self._normalizers.get(obj.kind)
        if fn:
            return fn(obj)
        return None, ArtifactGraph(graph_id=obj.object_id)


def default_normalizer_registry() -> NormalizerRegistry:
    reg = NormalizerRegistry()
    reg.register(SapObjectKind.CDS_VIEW, _normalize_cds)
    reg.register(SapObjectKind.CDS_STRUCTURE, _normalize_cds_structure)
    reg.register(SapObjectKind.TABLE, _normalize_ddic)
    reg.register(SapObjectKind.DATA_ELEMENT, _normalize_data_element)
    reg.register(SapObjectKind.DOMAIN, _normalize_domain)
    reg.register(SapObjectKind.PROGRAM, _normalize_abap)
    reg.register(SapObjectKind.ODATA_ENTITY, _normalize_odata_entity)
    reg.register(SapObjectKind.ODATA_ENTITY_SET, _normalize_odata_entity_set)
    reg.register(SapObjectKind.HANA_CALCULATION_VIEW, _normalize_hana)
    return reg


def _normalize_cds(obj: SapObject) -> tuple[CanonicalArtifact, ArtifactGraph]:
    meta = obj.raw_metadata.get("cds", {}) if obj.raw_metadata else {}
    graph = ArtifactGraph(graph_id=f"cds:{obj.object_id}")
    graph.add_node(
        GraphNode(
            node_id=obj.object_id,
            node_kind="artifact",
            label=obj.name,
            namespace="CDS::",
            artifact_type="cds.view",
        )
    )
    for table in meta.get("tables", []) or []:
        tid = f"DDIC::{table.upper()}"
        graph.add_node(GraphNode(node_id=tid, node_kind="dataset", label=table, namespace="DDIC::"))
        graph.add_edge(
            GraphEdge(
                edge_id=f"{obj.object_id}->reads->{tid}",
                source_id=obj.object_id,
                target_id=tid,
                relationship=RelationshipType.READS_FROM,
            )
        )
    artifact = CanonicalArtifact(
        identity=_identity_for(obj, "CDS::"),
        provenance=_base_provenance(obj, "cds", "1.0.0"),
        artifact_type="cds.view",
        name=obj.name,
        package=obj.package,
        source_path=str(obj.source_path or ""),
        metadata={"cds": meta},
        graph_fragment_id=graph.graph_id,
    )
    return artifact, graph


def _normalize_cds_structure(obj: SapObject) -> tuple[CanonicalArtifact, ArtifactGraph]:
    meta = obj.raw_metadata.get("cds_structure", {}) if obj.raw_metadata else {}
    graph = ArtifactGraph(graph_id=f"cds:struct:{obj.object_id}")
    graph.add_node(
        GraphNode(
            node_id=obj.object_id,
            node_kind="artifact",
            label=obj.name,
            namespace="CDS::",
            artifact_type="cds.structure",
        )
    )
    seen: set[str] = set()
    for comp in meta.get("components", []) or []:
        ctype = (comp.get("type_name") or "").upper()
        if not ctype or ctype in seen:
            continue
        seen.add(ctype)
        kind = comp.get("type_kind", "type")
        if kind == "structure":
            tid = f"CDS::STRUCT::{ctype}"
            rel = RelationshipType.CONTAINS
        else:
            tid = f"DDIC::TYPE::{ctype}"
            rel = RelationshipType.REFERENCES
        graph.add_node(GraphNode(node_id=tid, node_kind="artifact", label=ctype, namespace="CDIC::"))
        graph.add_edge(
            GraphEdge(
                edge_id=f"{obj.object_id}->{rel.value.lower()}->{tid}:{comp.get('name')}",
                source_id=obj.object_id,
                target_id=tid,
                relationship=rel,
                properties={"component": comp.get("name"), "type_kind": kind},
            )
        )
    artifact = CanonicalArtifact(
        identity=_identity_for(obj, "CDS::"),
        provenance=_base_provenance(obj, "cds.type_ddl", "1.0.0"),
        artifact_type="cds.structure",
        name=obj.name,
        package=obj.package,
        source_path=str(obj.source_path or ""),
        metadata={"cds_structure": meta},
        graph_fragment_id=graph.graph_id,
    )
    return artifact, graph


def _normalize_ddic(obj: SapObject) -> tuple[CanonicalArtifact, ArtifactGraph]:
    meta = obj.raw_metadata.get("ddic", {}) if obj.raw_metadata else {}
    graph = ArtifactGraph(graph_id=f"ddic:{obj.object_id}")
    graph.add_node(
        GraphNode(
            node_id=obj.object_id,
            node_kind="artifact",
            label=obj.name,
            namespace="DDIC::",
            artifact_type="ddic.table",
        )
    )
    for field in meta.get("fields", []) or []:
        ct = (field.get("check_table") or "").upper()
        if not ct:
            continue
        tid = f"DDIC::{ct}"
        graph.add_node(GraphNode(node_id=tid, node_kind="artifact", label=ct, namespace="DDIC::"))
        graph.add_edge(
            GraphEdge(
                edge_id=f"{obj.object_id}->ref->{tid}:{field.get('name')}",
                source_id=obj.object_id,
                target_id=tid,
                relationship=RelationshipType.REFERENCES,
                properties={"field": field.get("name")},
            )
        )
    artifact = CanonicalArtifact(
        identity=_identity_for(obj, "DDIC::"),
        provenance=_base_provenance(obj, "ddic", "1.0.0"),
        artifact_type="ddic.table",
        name=obj.name,
        package=obj.package,
        source_path=str(obj.source_path or ""),
        metadata={"ddic": meta},
        graph_fragment_id=graph.graph_id,
    )
    return artifact, graph


def _normalize_data_element(obj: SapObject) -> tuple[CanonicalArtifact, ArtifactGraph]:
    meta = obj.raw_metadata.get("data_element", {}) if obj.raw_metadata else {}
    graph = ArtifactGraph(graph_id=f"ddic:dtel:{obj.object_id}")
    graph.add_node(
        GraphNode(
            node_id=obj.object_id,
            node_kind="artifact",
            label=obj.name,
            namespace="DDIC::",
            artifact_type="ddic.data_element",
        )
    )
    type_name = (meta.get("type_name") or "").upper()
    if meta.get("type_kind") == "domain" and type_name:
        did = f"DDIC::DOMAIN::{type_name}"
        graph.add_node(GraphNode(node_id=did, node_kind="artifact", label=type_name, namespace="DDIC::"))
        graph.add_edge(
            GraphEdge(
                edge_id=f"{obj.object_id}->refs->{did}",
                source_id=obj.object_id,
                target_id=did,
                relationship=RelationshipType.REFERENCES,
                properties={"reference_type": "domain"},
            )
        )
    artifact = CanonicalArtifact(
        identity=_identity_for(obj, "DDIC::"),
        provenance=_base_provenance(obj, "ddic.adt", "1.0.0"),
        artifact_type="ddic.data_element",
        name=obj.name,
        package=obj.package or meta.get("package", ""),
        source_path=str(obj.source_path or ""),
        metadata={"data_element": meta},
        graph_fragment_id=graph.graph_id,
    )
    return artifact, graph


def _normalize_domain(obj: SapObject) -> tuple[CanonicalArtifact, ArtifactGraph]:
    meta = obj.raw_metadata.get("domain", {}) if obj.raw_metadata else {}
    graph = ArtifactGraph(graph_id=f"ddic:dom:{obj.object_id}")
    graph.add_node(
        GraphNode(
            node_id=obj.object_id,
            node_kind="artifact",
            label=obj.name,
            namespace="DDIC::",
            artifact_type="ddic.domain",
        )
    )
    value_table = (meta.get("value_table") or "").upper()
    if value_table:
        tid = f"DDIC::{value_table}"
        graph.add_node(GraphNode(node_id=tid, node_kind="dataset", label=value_table, namespace="DDIC::"))
        graph.add_edge(
            GraphEdge(
                edge_id=f"{obj.object_id}->refs->{tid}",
                source_id=obj.object_id,
                target_id=tid,
                relationship=RelationshipType.REFERENCES,
                properties={"reference_type": "value_table"},
            )
        )
    artifact = CanonicalArtifact(
        identity=_identity_for(obj, "DDIC::"),
        provenance=_base_provenance(obj, "ddic.adt", "1.0.0"),
        artifact_type="ddic.domain",
        name=obj.name,
        package=obj.package or meta.get("package", ""),
        source_path=str(obj.source_path or ""),
        metadata={"domain": meta},
        graph_fragment_id=graph.graph_id,
    )
    return artifact, graph


def _normalize_abap(obj: SapObject) -> tuple[CanonicalArtifact, ArtifactGraph]:
    meta = obj.raw_metadata.get("abap", {}) if obj.raw_metadata else {}
    graph = ArtifactGraph(graph_id=f"abap:{obj.object_id}")
    graph.add_node(
        GraphNode(
            node_id=obj.object_id,
            node_kind="artifact",
            label=obj.name,
            namespace="ABAP::",
            artifact_type="abap.program",
        )
    )
    for table in meta.get("tables", []) or []:
        tid = f"DDIC::{str(table).upper()}"
        graph.add_node(GraphNode(node_id=tid, node_kind="dataset", label=str(table), namespace="DDIC::"))
        graph.add_edge(
            GraphEdge(
                edge_id=f"{obj.object_id}->reads->{tid}",
                source_id=obj.object_id,
                target_id=tid,
                relationship=RelationshipType.READS_FROM,
            )
        )
    for fn in meta.get("functions", []) or []:
        fid = f"ABAP::FM:{fn}"
        graph.add_node(GraphNode(node_id=fid, node_kind="artifact", label=str(fn), namespace="ABAP::"))
        graph.add_edge(
            GraphEdge(
                edge_id=f"{obj.object_id}->calls->{fid}",
                source_id=obj.object_id,
                target_id=fid,
                relationship=RelationshipType.CALLS,
            )
        )
    seen_reads: set[str] = set()
    for vr in meta.get("view_references", []) or []:
        if not isinstance(vr, dict):
            continue
        name = str(vr.get("name", "")).upper()
        res = vr.get("resolution") or {}
        stable = res.get("resolved_stable_id") or vr.get("resolved_stable_id")
        if stable and stable not in seen_reads:
            seen_reads.add(stable)
            graph.add_edge(
                GraphEdge(
                    edge_id=f"{obj.object_id}->reads->{stable}",
                    source_id=obj.object_id,
                    target_id=stable,
                    relationship=RelationshipType.READS_FROM,
                    properties={
                        "view_kind": vr.get("kind"),
                        "confidence": res.get("confidence", vr.get("confidence")),
                        "resolution_strategy": res.get("resolution_strategy", "heuristic"),
                    },
                )
            )
            continue
        tid = f"DDIC::{name}" if vr.get("kind") == "ddic_table" else f"ABAP::REF::{name}"
        if tid in seen_reads:
            continue
        seen_reads.add(tid)
        graph.add_node(GraphNode(node_id=tid, node_kind="dataset", label=name, namespace="ABAP::"))
        graph.add_edge(
            GraphEdge(
                edge_id=f"{obj.object_id}->reads->{tid}",
                source_id=obj.object_id,
                target_id=tid,
                relationship=RelationshipType.READS_FROM,
                properties={"view_kind": vr.get("kind"), "confidence": vr.get("confidence", 0.5)},
            )
        )
    artifact = CanonicalArtifact(
        identity=_identity_for(obj, "ABAP::"),
        provenance=_base_provenance(obj, "abap", "1.0.0"),
        artifact_type="abap.program",
        name=obj.name,
        package=obj.package,
        source_path=str(obj.source_path or ""),
        metadata={"abap": meta},
        graph_fragment_id=graph.graph_id,
    )
    return artifact, graph


def _normalize_odata_entity(obj: SapObject) -> tuple[CanonicalArtifact, ArtifactGraph]:
    meta = obj.raw_metadata.get("odata", {}) if obj.raw_metadata else {}
    stable = meta.get("stable_id") or obj.object_id
    graph = ArtifactGraph(graph_id=f"odata:{stable}")
    graph.add_node(
        GraphNode(
            node_id=stable,
            node_kind="artifact",
            label=obj.name,
            namespace="ODATA::",
            artifact_type="odata.entity",
        )
    )
    for nav in meta.get("navigation", []) or []:
        target = (nav.get("target") or "").upper()
        if not target:
            continue
        tid = f"ODATA::{target}"
        graph.add_edge(
            GraphEdge(
                edge_id=f"{stable}->exposes->{tid}",
                source_id=stable,
                target_id=tid,
                relationship=RelationshipType.EXPOSES,
                properties={"name": nav.get("name"), "multiplicity": nav.get("multiplicity")},
            )
        )
    identity = ArtifactIdentity(
        stable_id=stable,
        physical_id=obj.name,
        semantic_id=obj.semantic_entity or "",
        display_id=obj.name,
        namespace="ODATA::",
    )
    artifact = CanonicalArtifact(
        identity=identity,
        provenance=_base_provenance(obj, "odata", "1.0.0"),
        artifact_type="odata.entity",
        name=obj.name,
        package=obj.package,
        source_path=str(obj.source_path or ""),
        metadata={"odata": meta},
        graph_fragment_id=graph.graph_id,
    )
    return artifact, graph


def _normalize_hana(obj: SapObject) -> tuple[CanonicalArtifact, ArtifactGraph]:
    from md_generator.sap.canonical.hana.calculation_view import CalculationView

    data = obj.raw_metadata.get("canonical") if obj.raw_metadata else None
    if data:
        cv = CalculationView.model_validate(data)
        frag_data = obj.raw_metadata.get("graph_fragment", {})
        graph = ArtifactGraph.model_validate(frag_data) if frag_data else ArtifactGraph(graph_id=cv.identity.stable_id)
        return cv, graph
    graph = ArtifactGraph(graph_id=f"hana:{obj.object_id}")
    graph.add_node(
        GraphNode(
            node_id=obj.object_id,
            node_kind="artifact",
            label=obj.name,
            namespace="HANA::",
            artifact_type="hana.calculation_view",
        )
    )
    artifact = CanonicalArtifact(
        identity=_identity_for(obj, "HANA::"),
        provenance=_base_provenance(obj, "hana.calculation_view", "1.0.0"),
        artifact_type="hana.calculation_view",
        name=obj.name,
        package=obj.package,
        source_path=str(obj.source_path or ""),
        metadata=obj.raw_metadata or {},
        graph_fragment_id=graph.graph_id,
    )
    return artifact, graph


def _normalize_odata_entity_set(obj: SapObject) -> tuple[CanonicalArtifact, ArtifactGraph]:
    meta = obj.raw_metadata or {}
    stable = obj.object_id
    graph = ArtifactGraph(graph_id=f"odata-es:{stable}")
    graph.add_node(
        GraphNode(
            node_id=stable,
            node_kind="artifact",
            label=obj.name,
            namespace="ODATA::",
            artifact_type="odata.entity_set",
        )
    )
    artifact = CanonicalArtifact(
        identity=_identity_for(obj, "ODATA::"),
        provenance=_base_provenance(obj, "odata", "1.0.0"),
        artifact_type="odata.entity_set",
        name=obj.name,
        package=obj.package,
        source_path=str(obj.source_path or ""),
        metadata=meta,
        graph_fragment_id=graph.graph_id,
    )
    return artifact, graph
