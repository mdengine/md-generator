from __future__ import annotations

import networkx as nx

from md_generator.sap.graph import relations as rel
from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.models.metadata.abap import AbapAnalysis
from md_generator.sap.models.metadata.cds import CdsAnalysis
from md_generator.sap.models.metadata.ddic import DdicTable


def _node_id(obj: SapObject) -> str:
    return obj.object_id


def build_sap_graph(objects: list[SapObject]) -> nx.MultiDiGraph:
    g: nx.MultiDiGraph = nx.MultiDiGraph()
    by_name: dict[str, SapObject] = {}
    for obj in objects:
        nid = _node_id(obj)
        g.add_node(
            nid,
            kind=obj.kind.value,
            name=obj.name,
            package=obj.package,
            semantic_entity=obj.semantic_entity,
        )
        by_name[obj.name.upper()] = obj

    for obj in objects:
        src = _node_id(obj)
        meta = obj.raw_metadata or {}

        if obj.kind == SapObjectKind.PROGRAM and "abap" in meta:
            abap = meta["abap"]
            if isinstance(abap, dict):
                for t in abap.get("tables", []):
                    tgt = _resolve_table_node(by_name, t)
                    if tgt:
                        g.add_edge(src, _node_id(tgt), relation=rel.READS_TABLE, table=t)
                for fn in abap.get("functions", []):
                    g.add_edge(src, f"FM:{fn}", relation=rel.CALLS, target=fn)
                    if f"FM:{fn}" not in g:
                        g.add_node(f"FM:{fn}", kind="FUNCTION_MODULE", name=fn)
                for inc in abap.get("includes", []):
                    g.add_edge(src, f"INC:{inc}", relation=rel.INCLUDES, target=inc)

        if obj.kind == SapObjectKind.CDS_VIEW and "cds" in meta:
            cds = meta["cds"]
            if isinstance(cds, dict):
                for a in cds.get("associations", []):
                    target = (a.get("target") or "").split(".")[-1].upper()
                    tgt = by_name.get(target)
                    edge_rel = rel.COMPOSITION if a.get("kind") == "composition" else rel.ASSOCIATION
                    if tgt:
                        g.add_edge(src, _node_id(tgt), relation=edge_rel, name=a.get("name"))

        if obj.kind == SapObjectKind.TABLE and "ddic" in meta:
            ddic = meta["ddic"]
            if isinstance(ddic, dict):
                for f in ddic.get("fields", []):
                    ct = (f.get("check_table") or "").upper()
                    if ct:
                        tgt = by_name.get(ct)
                        if tgt:
                            g.add_edge(src, _node_id(tgt), relation=rel.FK, field=f.get("name"))

        if obj.kind == SapObjectKind.BAPI and "bapi" in meta:
            bapi = meta["bapi"]
            if isinstance(bapi, dict):
                for p in bapi.get("parameters", []) or []:
                    pname = str(p.get("name", "")).upper()
                    if pname.endswith("_TAB") or pname in by_name:
                        tgt = by_name.get(pname.replace("_TAB", ""))
                        if tgt:
                            g.add_edge(src, _node_id(tgt), relation=rel.MASTER_TX)

        if obj.kind == SapObjectKind.ODATA_SERVICE:
            svc = obj.name
            for other in objects:
                if other.package.upper() == svc or other.package == obj.package:
                    if other.kind == SapObjectKind.ODATA_ENTITY_SET:
                        g.add_edge(src, _node_id(other), relation=rel.ODATA_ENTITY_SET)
                    elif other.kind == SapObjectKind.ODATA_ACTION:
                        g.add_edge(src, _node_id(other), relation=rel.ODATA_ACTION)

        if obj.kind == SapObjectKind.ODATA_ENTITY_SET:
            et_name = (meta.get("entity_type") or "").upper()
            tgt = by_name.get(et_name)
            if tgt:
                g.add_edge(src, _node_id(tgt), relation=rel.ODATA_ENTITY_SET)

        if obj.kind == SapObjectKind.ODATA_ENTITY and "odata" in meta:
            odata = meta["odata"]
            if isinstance(odata, dict):
                for nav in odata.get("navigation", []):
                    target = (nav.get("target") or "").upper()
                    mult = nav.get("multiplicity", "n")
                    tgt = by_name.get(target)
                    if tgt:
                        g.add_edge(
                            src,
                            _node_id(tgt),
                            relation=rel.NAV_PROP,
                            name=nav.get("name"),
                            multiplicity=mult,
                        )

    return g


def _resolve_table_node(by_name: dict[str, SapObject], table: str) -> SapObject | None:
    t = table.upper()
    if t in by_name:
        return by_name[t]
    for obj in by_name.values():
        if obj.kind == SapObjectKind.TABLE and obj.name == t:
            return obj
    return None


def enrich_from_parse_results(
    g: nx.MultiDiGraph,
    objects: list[SapObject],
) -> int:
  """Additional edges from typed metadata objects; returns edge count."""
  return g.number_of_edges()
