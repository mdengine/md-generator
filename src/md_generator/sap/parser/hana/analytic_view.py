from __future__ import annotations

from pathlib import Path

from md_generator.sap.parser.hana._variant_common import parse_hana_variant_xml


def parse_analytic_view(path: Path):
    return parse_hana_variant_xml(
        path,
        artifact_type="hana.analytic_view",
        execution_semantic="hana_analytic_view",
        xml_hint="analyticView",
        stable_prefix="HANA::AV",
    )
