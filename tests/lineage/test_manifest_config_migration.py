from __future__ import annotations

import json
import pytest

from md_generator.lineage.manifest import (
    DeltaState,
    DeltaReason,
    ManifestEntry,
    VersionedManifest,
    evaluate_delta,
)
from md_generator.vector.exceptions import TenantBoundaryError


def test_manifest_v1_0_backward_compatible_deserialization():
    legacy_json = json.dumps({
        "manifest_schema_version": "1.0",
        "pipeline_version": "1.0",
        "semantic_schema_version": "1.0",
        "chunker_version": "1.0",
        "security_policy_version": "1.0",
        "embedding_provider": "fastembed",
        "embedding_model": "bge-small",
        "embedding_dimension": 384,
        "distance_metric": "cosine",
        "timestamp": 1234567.8,
        "entries": {
            "file:///test.py": {
                "document_id": "a" * 64,
                "revision_id": "b" * 64,
                "source_uri": "file:///test.py",
                "content_hash": "c" * 64,
                "state": "UNCHANGED",
            }
        }
    })

    # Must deserialize cleanly without schema errors
    manifest = VersionedManifest.from_json(legacy_json)
    assert manifest.manifest_schema_version == "1.0"
    assert manifest.config_fingerprint == "__unknown__"
    assert "file:///test.py" in manifest.entries


def test_manifest_v1_1_serialization_roundtrip():
    entry = ManifestEntry(
        document_id="a" * 64,
        revision_id="b" * 64,
        source_uri="file:///test.py",
        content_hash="c" * 64,
        state=DeltaState.UNCHANGED,
    )
    manifest = VersionedManifest(
        manifest_schema_version="1.1",
        config_fingerprint="fp_" + "1" * 60,
        tenant_id="tenant_alpha",
        entries={"file:///test.py": entry},
    )

    data = manifest.to_dict()
    assert data["manifest_schema_version"] == "1.1"
    assert data["config_fingerprint"] == "fp_" + "1" * 60
    assert data["tenant_id"] == "tenant_alpha"

    restored = VersionedManifest.from_dict(data)
    assert restored.config_fingerprint == "fp_" + "1" * 60
    assert restored.tenant_id == "tenant_alpha"


def test_config_delta_invalidation_triggers_config_changed():
    prev_manifest = VersionedManifest(
        manifest_schema_version="1.1",
        config_fingerprint="cfg_old_1111",
        tenant_id="tenant_prod",
        entries={
            "file:///app.py": ManifestEntry(
                document_id="doc1",
                revision_id="rev_old",
                source_uri="file:///app.py",
                content_hash="hash_same_1234",
                state=DeltaState.UNCHANGED,
            )
        }
    )

    current_files = {
        "file:///app.py": {
            "document_id": "doc1",
            "revision_id": "rev_new",
            "content_hash": "hash_same_1234",
        }
    }

    # When config changed, state must be MODIFIED with reason CONFIG_CHANGED
    delta = evaluate_delta(
        previous_manifest=prev_manifest,
        current_files=current_files,
        current_config_hash="cfg_new_2222",
        current_tenant="tenant_prod",
    )

    entry = delta["file:///app.py"]
    assert entry.state == DeltaState.MODIFIED
    assert entry.reason == DeltaReason.CONFIG_CHANGED


def test_legacy_v1_0_unknown_config_triggers_reconciliation():
    legacy_manifest = VersionedManifest(
        manifest_schema_version="1.0",
        config_fingerprint="__unknown__",
        entries={
            "file:///app.py": ManifestEntry(
                document_id="doc1",
                revision_id="rev_old",
                source_uri="file:///app.py",
                content_hash="hash_same_1234",
                state=DeltaState.UNCHANGED,
            )
        }
    )

    current_files = {
        "file:///app.py": {
            "document_id": "doc1",
            "revision_id": "rev_new",
            "content_hash": "hash_same_1234",
        }
    }

    # Default policy: reprocess unknown configuration
    delta = evaluate_delta(
        previous_manifest=legacy_manifest,
        current_files=current_files,
        current_config_hash="cfg_verified_1234",
        reprocess_unknown_config=True,
    )

    entry = delta["file:///app.py"]
    assert entry.state == DeltaState.MODIFIED
    assert entry.reason == DeltaReason.CONFIG_CHANGED


def test_cross_tenant_mismatch_raises_tenant_boundary_error():
    tenant_a_manifest = VersionedManifest(
        manifest_schema_version="1.1",
        config_fingerprint="cfg_1234",
        tenant_id="tenant_A",
        entries={}
    )

    with pytest.raises(TenantBoundaryError, match="Cross-tenant operation rejected"):
        evaluate_delta(
            previous_manifest=tenant_a_manifest,
            current_files={},
            current_config_hash="cfg_1234",
            current_tenant="tenant_B",
        )

