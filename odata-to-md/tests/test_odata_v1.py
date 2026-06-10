from __future__ import annotations

from pathlib import Path

from md_generator.odata.models.domain import ODataVersion
from md_generator.odata.parser.detector import detect_format, detect_version
from md_generator.odata.parser.registry import parse_document

FIXTURES = Path(__file__).parent / "fixtures" / "odata"


def test_detect_v1():
    p = FIXTURES / "v1_metadata.xml"
    fmt = detect_format(p)
    ver = detect_version(p, fmt)
    assert ver == ODataVersion.V1


def test_v1_parses_entity_types():
    doc = parse_document(FIXTURES / "v1_metadata.xml")
    assert doc.odata_version == ODataVersion.V1
    names = {e.name for e in doc.entity_types}
    assert "Account" in names
    assert "Ledger" in names
    assert all(e.stable_id.startswith("odata:v1_0:") for e in doc.entity_types)
