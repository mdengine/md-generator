from __future__ import annotations

from pathlib import Path

from md_generator.sap.parser.hana._variant_common import parse_hana_variant_xml


def parse_attribute_view(path: Path):
    return parse_hana_variant_xml(
        path,
        artifact_type="hana.attribute_view",
        execution_semantic="hana_attribute_view",
        xml_hint="attributeView",
        stable_prefix="HANA::ATV",
    )
