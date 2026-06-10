from __future__ import annotations

from pathlib import Path

from md_generator.sap.parser.hana._variant_common import parse_hana_variant_text


def parse_sql_view(path: Path):
    return parse_hana_variant_text(
        path,
        artifact_type="hana.sql_view",
        execution_semantic="hana_sql_view",
        stable_prefix="HANA::SQL",
    )
