from md_generator.sap.canonical.loader import load_canonical
from md_generator.sap.parser.hana.calculation_view import parse_calculation_view_xml
from pathlib import Path


def test_canonical_loader_hana():
    path = Path(__file__).parent / "fixtures" / "hana" / "cv_sales.xml"
    if not path.is_file():
        return
    cv, _ = parse_calculation_view_xml(path)
    data = cv.model_dump(mode="json")
    loaded = load_canonical(data)
    assert loaded.artifact_type == "hana.calculation_view"
