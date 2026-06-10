from __future__ import annotations

from pathlib import Path

from md_generator.sap.parser.hana._variant_common import parse_hana_variant_text


def parse_hdi_cv(path: Path):
    return parse_hana_variant_text(
        path,
        artifact_type="hana.hdi_calculation_view",
        execution_semantic="hana_hdi_cv",
        stable_prefix="HANA::HDI",
    )
