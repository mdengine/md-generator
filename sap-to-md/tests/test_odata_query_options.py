from __future__ import annotations

from pathlib import Path

from md_generator.sap.core.extractor import extract_to_markdown
from md_generator.sap.core.run_config import SapRunConfig
from md_generator.sap.parser.odata.registry import parse_document

FIXTURES = Path(__file__).parent / "fixtures" / "odata"


def test_entity_set_query_options_section(tmp_path: Path):
    doc = parse_document(FIXTURES / "v4_metadata.xml")
    from md_generator.sap.markdown.builders.odata_builder import _render_entity_set

    md = _render_entity_set(doc, doc.entity_sets[0])
    assert "## Supported Query Options" in md
    assert "$search" in md
    assert "## CRUD capabilities" in md
    assert "Insert: True" in md


def test_defaults_when_no_capabilities():
    doc = parse_document(FIXTURES / "v2_with_container.xml")
    from md_generator.sap.markdown.builders.odata_builder import _render_entity_set

    md = _render_entity_set(doc, doc.entity_sets[0])
    assert "$filter" in md
    assert "$select" in md
