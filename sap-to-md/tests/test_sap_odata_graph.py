from __future__ import annotations

from pathlib import Path

from md_generator.sap.graph import relations as rel
from md_generator.sap.graph.builder import build_sap_graph
from md_generator.sap.parser.base import ParseContext
from md_generator.sap.parser.odata.parser import ODataParserPlugin

FIXTURES = Path(__file__).parent / "fixtures" / "odata"


def test_sap_nav_edges_have_multiplicity():
    result = ODataParserPlugin().parse(FIXTURES / "v2_with_container.xml", ParseContext(root=FIXTURES))
    g = build_sap_graph(result.objects)
    nav_edges = [
        d
        for _u, _v, _k, d in g.edges(keys=True, data=True)
        if d.get("relation") == rel.NAV_PROP
    ]
    assert nav_edges
    assert any(d.get("multiplicity") == "n" for d in nav_edges)
