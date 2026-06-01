from __future__ import annotations

from pathlib import Path

from md_generator.sap.markdown.chunking.registry import get_strategies
from md_generator.sap.parser.base import ParseContext
from md_generator.sap.parser.odata.parser import ODataParserPlugin
from md_generator.sap.parser.odata.registry import parse_document

FIXTURES = Path(__file__).parent / "fixtures" / "odata"


def test_odata_chunk_strategies():
    result = ODataParserPlugin().parse(FIXTURES / "v2_with_container.xml", ParseContext(root=FIXTURES))
    doc = parse_document(FIXTURES / "v2_with_container.xml")
    strategies = get_strategies(["odata_service", "odata_entity_set", "odata_index", "odata_capabilities"])
    chunks = []
    for strat in strategies:
        chunks.extend(list(strat.iter_chunks(result.objects, odata_documents=[doc])))
    types = {c.chunk_type for c in chunks}
    assert "odata_service" in types
    assert "odata_entity_set" in types
    assert "odata_index" in types
    assert "odata_capabilities" in types
