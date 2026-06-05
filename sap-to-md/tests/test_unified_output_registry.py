from __future__ import annotations

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.identity import ArtifactIdentity
from md_generator.sap.canonical.provenance import ProvenanceBundle
from md_generator.sap.core.link_graph import SapLinkGraph
from md_generator.sap.markdown.unified_output_registry import (
    UnifiedOutputRegistry,
    build_unified_output_registry,
)


def _artifact(name: str, artifact_type: str, package: str = "SZS") -> CanonicalArtifact:
    return CanonicalArtifact(
        identity=ArtifactIdentity.from_legacy(
            stable_id=f"DDIC::{artifact_type}::{name}",
            name=name,
            namespace="DDIC::",
        ),
        provenance=ProvenanceBundle(parser_id="test", parser_version="1"),
        artifact_type=artifact_type,
        name=name,
        package=package,
        metadata={},
    )


def test_register_artifact_paths():
    reg = UnifiedOutputRegistry()
    art = _artifact("CHAR100", "ddic.data_element")
    reg.register_artifact(art, entity_path="entities/szs_char100.md")
    entry = reg.entries[art.identity.stable_id]
    assert entry.canonical_path == "ddic/data-elements/char100.md"
    assert entry.entity_path == "entities/szs_char100.md"
    assert reg.path_registry[("DATA_ELEMENT", "CHAR100")] == "ddic/data-elements/char100.md"


def test_build_unified_output_registry_with_link_graph():
    lg = SapLinkGraph()
    lg.register("data_element", "SZS", "CHAR100", "entities/szs_char100.md")
    art = _artifact("CHAR100", "ddic.data_element")
    reg = build_unified_output_registry([art], lg)
    assert reg.entries[art.identity.stable_id].entity_path == "entities/szs_char100.md"
    assert lg.canonical_path_for("DATA_ELEMENT", "CHAR100") == "ddic/data-elements/char100.md"
