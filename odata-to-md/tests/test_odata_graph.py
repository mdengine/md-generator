from __future__ import annotations

from pathlib import Path

from md_generator.odata.generators import relations as rel
from md_generator.odata.generators.graph_builder import build_odata_graph
from md_generator.odata.parser.registry import parse_document

FIXTURES = Path(__file__).parent / "fixtures" / "odata"


def test_nav_edges_have_multiplicity():
    doc = parse_document(FIXTURES / "v2_with_container.xml")
    g = build_odata_graph([doc])
    nav_edges = [
        (u, v, d)
        for u, v, _k, d in g.edges(keys=True, data=True)
        if d.get("relation") == rel.NAV_PROP
    ]
    assert nav_edges
    assert any(d.get("multiplicity") == "n" for _u, _v, d in nav_edges)


def test_entity_set_edges_use_stable_ids():
    doc = parse_document(FIXTURES / "v2_with_container.xml")
    g = build_odata_graph([doc])
    es_edges = [
        d for _u, _v, _k, d in g.edges(keys=True, data=True) if d.get("relation") == rel.ODATA_ENTITY_SET
    ]
    assert es_edges
    node_ids = set(g.nodes)
    assert any(str(n).startswith("odata:") for n in node_ids)
