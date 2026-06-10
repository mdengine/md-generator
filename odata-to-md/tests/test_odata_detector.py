from __future__ import annotations

from pathlib import Path

from md_generator.odata.parser.detector import detect_format, detect_version
from md_generator.odata.models.domain import ODataFormat, ODataVersion
from md_generator.odata.parser.registry import parse_document

FIXTURES = Path(__file__).parent / "fixtures" / "odata"


def test_detect_v2():
    p = FIXTURES / "metadata.xml"
    fmt = detect_format(p)
    ver = detect_version(p, fmt)
    assert fmt == ODataFormat.EDMX_XML
    assert ver == ODataVersion.V2


def test_stable_ids_unique():
    doc = parse_document(FIXTURES / "v2_with_container.xml")
    ids = [e.stable_id for e in doc.entity_types] + [s.stable_id for s in doc.entity_sets]
    assert len(ids) == len(set(ids))
    assert all(i.startswith("odata:") for i in ids)


def test_v2_entity_sets():
    doc = parse_document(FIXTURES / "v2_with_container.xml")
    assert len(doc.entity_sets) == 2
    assert doc.entity_sets[0].name == "Customers"


def test_nav_multiplicity():
    doc = parse_document(FIXTURES / "v2_with_container.xml")
    customer = next(e for e in doc.entity_types if e.name == "Customer")
    orders_nav = next(n for n in customer.navigation_properties if n.name == "Orders")
    assert orders_nav.target_type == "Order"
    assert orders_nav.multiplicity == "n"
