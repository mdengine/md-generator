from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.canonical.identity import ArtifactIdentity
from md_generator.sap.canonical.provenance import ProvenanceBundle
from md_generator.sap.markdown.unified_output_registry import UnifiedOutputRegistry


def test_navigation_index_schema(tmp_path: Path):
    reg = UnifiedOutputRegistry()
    art = CanonicalArtifact(
        identity=ArtifactIdentity.from_legacy(
            stable_id="DDIC::DATA_ELEMENT::CHAR100",
            name="CHAR100",
            namespace="DDIC::",
        ),
        provenance=ProvenanceBundle(parser_id="test", parser_version="1"),
        artifact_type="ddic.data_element",
        name="CHAR100",
        metadata={},
    )
    reg.register_artifact(art, entity_path="entities/szs_char100.md")
    path = reg.write_navigation_index(tmp_path, run_id="run-1")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0.0"
    assert data["run_id"] == "run-1"
    assert len(data["entries"]) == 1
    entry = data["entries"][0]
    assert entry["name"] == "CHAR100"
    assert entry["kind"] == "DATA_ELEMENT"
    assert entry["stable_id"] == "DDIC::DATA_ELEMENT::CHAR100"
    assert entry["paths"]["entity"] == "entities/szs_char100.md"
    assert entry["paths"]["canonical"] == "ddic/data-elements/char100.md"
    assert "generated_at" in data
