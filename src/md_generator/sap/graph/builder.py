from __future__ import annotations

import networkx as nx

from md_generator.sap.graph import relations as rel
from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.parser.abap.view_resolver import _resolve_object


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
                seen_targets: set[str] = set()
                for vr in abap.get("view_references", []) or []:
                    if not isinstance(vr, dict):
                        continue
                    name = vr.get("name", "")
                    schema = vr.get("schema", "")
                    tgt_obj = _resolve_object(by_name, name, schema)
                    if tgt_obj:
                        tid = _node_id(tgt_obj)
                        if tid in seen_targets:
                            continue
                        seen_targets.add(tid)
                        res = vr.get("resolution") or {}
                        g.add_edge(
                            src,
                            tid,
                            relation=rel.READS_TABLE,
                            view_kind=vr.get("kind"),
                            confidence=res.get("confidence", vr.get("confidence")),
                            resolution_strategy=res.get("resolution_strategy"),
                        )
                for stmt in abap.get("sql_statements", []) or []:
                    fp = (stmt.get("fingerprint") or "")[:8]
                    if not fp and stmt.get("text"):
                        import hashlib
                        fp = hashlib.sha256(str(stmt["text"]).encode(errors="ignore")).hexdigest()[:8]
                    stmt_id = stmt.get("stable_id") or f"SQL::{src}::{fp or 'unknown'}::{stmt.get('line', 0)}"
                    g.add_node(
                        stmt_id,
                        kind="sql_statement",
                        name=f"{stmt.get('statement_kind','SQL')} @ line {stmt.get('line',0)}",
                    )
                    g.add_edge(src, stmt_id, relation=rel.EXECUTES)
                    for t in stmt.get("objects", []) or []:
                        tgt = _resolve_table_node(by_name, t)
                        if tgt:
                            g.add_edge(stmt_id, _node_id(tgt), relation=rel.READS_TABLE)

        if obj.kind == SapObjectKind.CDS_VIEW and "cds" in meta:
            cds = meta["cds"]
            if isinstance(cds, dict):
                for a in cds.get("associations", []):
                    target = (a.get("target") or "").split(".")[-1].upper()
                    tgt = by_name.get(target)
                    edge_rel = rel.COMPOSITION if a.get("kind") == "composition" else rel.ASSOCIATION
                    if tgt:
                        g.add_edge(src, _node_id(tgt), relation=edge_rel, name=a.get("name"))

        if obj.kind == SapObjectKind.CDS_STRUCTURE and "cds_structure" in meta:
            st = meta["cds_structure"]
            if isinstance(st, dict):
                for comp in st.get("components", []):
                    ctype = (comp.get("type_name") or "").upper()
                    tgt = by_name.get(ctype)
                    if tgt:
                        edge_rel = rel.COMPOSITION if comp.get("type_kind") == "structure" else rel.ASSOCIATION
                        g.add_edge(src, _node_id(tgt), relation=edge_rel, component=comp.get("name"))

        if obj.kind == SapObjectKind.TABLE and "ddic" in meta:
            ddic = meta["ddic"]
            if isinstance(ddic, dict):
                for f in ddic.get("fields", []):
                    ct = (f.get("check_table") or "").upper()
                    if ct:
                        tgt = by_name.get(ct)
                        if tgt:
                            g.add_edge(src, _node_id(tgt), relation=rel.FK, field=f.get("name"))

        if obj.kind == SapObjectKind.DATA_ELEMENT and "data_element" in meta:
            de = meta["data_element"]
            if isinstance(de, dict):
                type_kind = de.get("type_kind", "")
                type_name = (de.get("type_name") or "").upper()
                resolved = de.get("resolved_type") or {}
                tgt = by_name.get(type_name)
                if tgt and type_kind:
                    g.add_edge(src, _node_id(tgt), relation=rel.FK, reference=type_kind)

        if obj.kind == SapObjectKind.STRUCTURE and "structure" in meta:
            st = meta["structure"]
            if isinstance(st, dict):
                for comp in st.get("components", []):
                    de = (comp.get("data_element") or "").upper()
                    tgt = by_name.get(de)
                    if tgt:
                        g.add_edge(src, _node_id(tgt), relation=rel.ASSOCIATION, component=comp.get("name"))

        if obj.kind == SapObjectKind.TABLE_TYPE and "table_type" in meta:
            tt = meta["table_type"]
            if isinstance(tt, dict):
                for key in ("row_type", "line_type"):
                    tname = (tt.get(key) or "").upper()
                    tgt = by_name.get(tname)
                    if tgt:
                        g.add_edge(src, _node_id(tgt), relation=rel.ASSOCIATION, ref=key)

        if obj.kind == SapObjectKind.RANGE_TYPE and "range_type" in meta:
            rt = meta["range_type"]
            if isinstance(rt, dict):
                for key in ("data_element", "domain"):
                    tname = (rt.get(key) or "").upper()
                    tgt = by_name.get(tname)
                    if tgt:
                        g.add_edge(src, _node_id(tgt), relation=rel.FK, ref=key)

        if obj.kind == SapObjectKind.REFERENCE_TYPE and "reference_type" in meta:
            rt = meta["reference_type"]
            if isinstance(rt, dict):
                for key in ("referenced_type", "check_table"):
                    tname = (rt.get(key) or "").upper()
                    tgt = by_name.get(tname)
                    if tgt:
                        g.add_edge(src, _node_id(tgt), relation=rel.FK, ref=key)

        if obj.kind == SapObjectKind.DOMAIN and "domain" in meta:
            dom = meta["domain"]
            if isinstance(dom, dict):
                vt = (dom.get("value_table") or "").upper()
                if vt:
                    tgt = by_name.get(vt)
                    if tgt:
                        g.add_edge(src, _node_id(tgt), relation=rel.FK, reference="value_table")

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
