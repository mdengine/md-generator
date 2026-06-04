from __future__ import annotations

from pathlib import Path

from md_generator.sap.framework.capabilities import ParserCapability
from md_generator.sap.parser.base import ParseContext, SapParseResult, SapParserPlugin
from md_generator.sap.parser.hana.analytic_view import parse_analytic_view
from md_generator.sap.parser.hana.attribute_view import parse_attribute_view
from md_generator.sap.parser.hana.hdi_calculation_view import parse_hdi_cv
from md_generator.sap.parser.hana.sql_view import parse_sql_view


class HanaParserPlugin(SapParserPlugin):
    name = "hana"
    version = "1.0.0"

    def capabilities(self) -> ParserCapability:
        return ParserCapability(
            lineage=True,
            sql_generation="yes",
            impact_analysis=True,
            semantic_id=True,
            transformation_graph=True,
        )

    def can_parse(self, path: Path) -> bool:
        return _detect_kind(path) is not None

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult | None:
        kind = _detect_kind(path)
        if kind == "calculation_view":
            from md_generator.sap.parser.hana.calculation_view import HanaCalculationViewParser

            return HanaCalculationViewParser().parse(path, ctx)
        if kind == "analytic_view":
            return parse_analytic_view(path)
        if kind == "attribute_view":
            return parse_attribute_view(path)
        if kind == "hdi_cv":
            return parse_hdi_cv(path)
        if kind == "sql_view":
            return parse_sql_view(path)
        return None


def _detect_kind(path: Path) -> str | None:
    from md_generator.sap.parser.odata.parser import _is_odata_metadata

    if _is_odata_metadata(path):
        return None
    suf = path.suffix.lower()
    if suf == ".hdbcalculationview":
        return "hdi_cv"
    if suf == ".hdbview":
        return "sql_view"
    if suf == ".sql":
        try:
            head = path.read_text(encoding="utf-8", errors="ignore")[:2048].upper()
            if "CREATE VIEW" in head or "CREATE OR REPLACE VIEW" in head:
                return "sql_view"
        except OSError:
            pass
        return None
    if suf not in {".xml", ".calculationview"}:
        return None
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:4096].lower()
    except OSError:
        return None
    if "calculation:scenario" in head or "<calculationscenario" in head:
        return "calculation_view"
    if "analyticview" in head or "analytic:view" in head:
        return "analytic_view"
    if "attributeview" in head or "attribute:view" in head:
        return "attribute_view"
    return None


class HanaCalculationViewParserPlugin(HanaParserPlugin):
    name = "hana.calculation_view"
