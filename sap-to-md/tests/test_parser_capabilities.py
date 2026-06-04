from md_generator.sap.parser.hana.calculation_view import HanaCalculationViewParser
from md_generator.sap.parser.bw.dtp import BwDtpParser


def test_parser_capabilities_hana():
    cap = HanaCalculationViewParser().capabilities()
    assert cap.lineage is True
    assert cap.transformation_graph is True


def test_parser_capabilities_bw():
    cap = BwDtpParser().capabilities()
    assert cap.impact_analysis is True
