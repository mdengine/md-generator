from __future__ import annotations

import json
from pathlib import Path

import pytest

from md_generator.sap.parser.hana.calculation_view import parse_calculation_view_xml


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "hana" / "cv_sales.xml"


@pytest.mark.skipif(not FIXTURE.is_file(), reason="HANA fixture missing")
def test_hana_cv_parse_golden():
    cv, graph = parse_calculation_view_xml(FIXTURE)
    assert cv.name == "CV_SALES"
    assert cv.schema == "SALES"
    assert len(cv.data_sources) == 2
    assert cv.transformation_graph is not None
    assert len(cv.transformation_graph.nodes) >= 3
    assert cv.identity.namespace == "HANA::"
    assert len(graph.edges) >= 2
    assert any(e.relationship.value == "READS_FROM" for e in graph.edges.values())


@pytest.mark.skipif(not FIXTURE.is_file(), reason="HANA fixture missing")
def test_hana_cv_canonical_json_serializable():
    cv, _ = parse_calculation_view_xml(FIXTURE)
    payload = cv.model_dump(mode="json")
    text = json.dumps(payload)
    assert "CV_SALES" in text
