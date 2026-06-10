from __future__ import annotations

from md_generator.sap.markdown.builders.renderer_context import (
    RendererContext,
    build_path_registry,
    link_for,
    link_for_type_reference,
    md_link,
)
from md_generator.sap.markdown.builders.ddic_sections import format_data_element
from md_generator.sap.markdown.builders.ddic_adapters import data_element_view_from_raw
from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.identity import ArtifactIdentity
from md_generator.sap.canonical.provenance import ProvenanceBundle


def _artifact(artifact_type: str, name: str) -> CanonicalArtifact:
    return CanonicalArtifact(
        identity=ArtifactIdentity.from_legacy(stable_id=f"x:{name}", name=name, namespace="DDIC::"),
        provenance=ProvenanceBundle(parser_id="test", parser_version="1.0.0", artifact_version=name),
        artifact_type=artifact_type,
        name=name,
        metadata={},
    )


def test_build_path_registry():
    arts = [
        _artifact("ddic.data_element", "CHAR100"),
        _artifact("ddic.domain", "CHAR100"),
        _artifact("ddic.structure", "BAL_S_CONT"),
    ]
    reg = build_path_registry(arts)
    assert reg[("DATA_ELEMENT", "CHAR100")] == "ddic/data-elements/char100.md"
    assert reg[("DOMAIN", "CHAR100")] == "ddic/domains/char100.md"
    assert reg[("STRUCTURE", "BAL_S_CONT")] == "structures/bal_s_cont.md"


def test_link_for_hit():
    ctx = RendererContext(path_registry={("DOMAIN", "CHAR100"): "ddic/domains/char100.md"})
    assert link_for("DOMAIN", "CHAR100", ctx) == "ddic/domains/char100.md"
    assert link_for("DOMAIN", "MISSING", ctx) is None


def test_link_for_type_reference():
    ctx = RendererContext(path_registry={
        ("STRUCTURE", "BAL_S_CONT"): "structures/bal_s_cont.md",
    })
    assert link_for_type_reference("structure", "BAL_S_CONT", ctx) == "structures/bal_s_cont.md"


def test_md_link_with_path():
    assert md_link("CHAR100", "ddic/domains/char100.md") == "[CHAR100](ddic/domains/char100.md)"
    assert md_link("CHAR100", None) == "`CHAR100`"


def test_formatter_emits_link():
    ctx = RendererContext(path_registry={("DOMAIN", "CHAR100"): "ddic/domains/char100.md"})
    view = data_element_view_from_raw({
        "name": "CHAR100",
        "type_kind": "domain",
        "type_name": "CHAR100",
        "data_type": "CHAR",
        "data_type_length": 100,
    })
    md = format_data_element(view, ctx)
    assert "[CHAR100](ddic/domains/char100.md)" in md
