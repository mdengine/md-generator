"""Contract Tests for VersionedManifest Serialization and Entries."""

import pytest
from md_generator.semantic.model.schema import InvalidSchemaError
from md_generator.lineage import (
    DeltaState,
    DeltaReason,
    ManifestEntry,
    VersionedManifest,
)


def test_manifest_entry_serialization():
    entry = ManifestEntry(
        document_id="a" * 64,
        revision_id="b" * 64,
        source_uri="file:///main.py",
        content_hash="c" * 64,
        state=DeltaState.NEW,
        reason=DeltaReason.CREATED,
    )
    d = entry.to_dict()
    assert d["state"] == "NEW"
    assert d["reason"] == "CREATED"

    reconstructed = ManifestEntry.from_dict(d)
    assert reconstructed.state == DeltaState.NEW
    assert reconstructed.reason == DeltaReason.CREATED


def test_versioned_manifest_roundtrip():
    entry1 = ManifestEntry(
        document_id="a" * 64,
        revision_id="b" * 64,
        source_uri="file:///app.py",
        content_hash="c" * 64,
        state=DeltaState.UNCHANGED,
    )
    manifest = VersionedManifest(
        embedding_provider="fastembed",
        embedding_model="BAAI/bge-small-en-v1.5",
        embedding_dimension=384,
        entries={"file:///app.py": entry1},
    )

    json_str = manifest.to_json()
    reconstructed = VersionedManifest.from_json(json_str)
    assert reconstructed.embedding_provider == "fastembed"
    assert "file:///app.py" in reconstructed.entries
    assert reconstructed.entries["file:///app.py"].state == DeltaState.UNCHANGED
