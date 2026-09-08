from __future__ import annotations

from pathlib import Path

from md_generator.sap.parser.base import ParseContext
from md_generator.sap.parser.datasphere.analytical_model import DatasphereAnalyticalModelParser
from md_generator.sap.parser.datasphere.data_flow import DatasphereDataFlowParser
from md_generator.sap.parser.datasphere.view import DatasphereViewParser
from md_generator.sap.canonical.datasphere.analytical_model import DatasphereAnalyticalModel
from md_generator.sap.canonical.datasphere.data_flow import DatasphereDataFlow
from md_generator.sap.canonical.datasphere.view import DatasphereView
from md_generator.sap.canonical.loader import load_canonical

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "datasphere" / "synthetic"


def test_datasphere_analytical_model_golden():
    path = FIXTURES_DIR / "analytical_model_sales.json"
    result = DatasphereAnalyticalModelParser().parse(path, ParseContext(root=FIXTURES_DIR))
    assert result and result.objects
    canonical_data = result.objects[0].raw_metadata["canonical"]
    artifact = load_canonical(canonical_data)
    assert isinstance(artifact, DatasphereAnalyticalModel)
    assert artifact.name == "AM_SALES"
    assert "REVENUE" in artifact.measures


def test_datasphere_data_flow_golden():
    path = FIXTURES_DIR / "data_flow_sales.json"
    result = DatasphereDataFlowParser().parse(path, ParseContext(root=FIXTURES_DIR))
    assert result and result.objects
    canonical_data = result.objects[0].raw_metadata["canonical"]
    artifact = load_canonical(canonical_data)
    assert isinstance(artifact, DatasphereDataFlow)
    assert artifact.name == "DF_SALES"
    assert len(artifact.steps) == 2
    assert artifact.steps[0]["object"] == "VIEW_SALES"


def test_datasphere_view_golden():
    path = FIXTURES_DIR / "ds_view_sales.json"
    result = DatasphereViewParser().parse(path, ParseContext(root=FIXTURES_DIR))
    assert result and result.objects
    canonical_data = result.objects[0].raw_metadata["canonical"]
    artifact = load_canonical(canonical_data)
    assert isinstance(artifact, DatasphereView)
    assert artifact.name == "VIEW_SALES"
    assert len(artifact.columns) == 2
    assert artifact.columns[0] == "REVENUE"
