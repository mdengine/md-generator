from __future__ import annotations

from pathlib import Path

from md_generator.sap.parser.odata.registry import parse_document

FIXTURES = Path(__file__).parent / "fixtures" / "odata"


def test_stable_id_format():
    doc = parse_document(FIXTURES / "metadata.xml")
    for entity in doc.entity_types:
        assert entity.stable_id.startswith("odata:")
        assert ":entity:" in entity.stable_id


def test_stable_ids_unique_within_document():
    doc = parse_document(FIXTURES / "v2_with_container.xml")
    ids = [e.stable_id for e in doc.entity_types] + [s.stable_id for s in doc.entity_sets]
    assert len(ids) == len(set(ids))


def test_stable_ids_deterministic_across_files():
    a = parse_document(FIXTURES / "metadata.xml")
    b = parse_document(FIXTURES / "v2_with_container.xml")
    a_customer = next(e for e in a.entity_types if e.name == "Customer")
    b_customer = next(e for e in b.entity_types if e.name == "Customer")
    assert a_customer.stable_id == b_customer.stable_id
