"""Contract Tests for 5-State Delta Lifecycle Evaluator & DeltaReason."""

import pytest
from md_generator.lineage import (
    DeltaState,
    DeltaReason,
    ManifestEntry,
    VersionedManifest,
    evaluate_delta,
)


def test_delta_evaluator_new_unchanged_modified_deleted():
    old_entry1 = ManifestEntry(
        document_id="1" * 64,
        revision_id="r1" + "0" * 62,
        source_uri="file:///file1.py",
        content_hash="h1" + "0" * 62,
        state=DeltaState.UNCHANGED,
    )
    old_entry2 = ManifestEntry(
        document_id="2" * 64,
        revision_id="r2" + "0" * 62,
        source_uri="file:///file2.py",
        content_hash="h2" + "0" * 62,
        state=DeltaState.UNCHANGED,
    )
    prev_manifest = VersionedManifest(entries={"file:///file1.py": old_entry1, "file:///file2.py": old_entry2})

    current_files = {
        "file:///file1.py": {
            "document_id": "1" * 64,
            "revision_id": "r1" + "0" * 62,
            "content_hash": "h1" + "0" * 62,  # Same hash -> UNCHANGED
        },
        "file:///file3.py": {
            "document_id": "3" * 64,
            "revision_id": "r3" + "0" * 62,
            "content_hash": "h3" + "0" * 62,  # New file -> NEW / CREATED
        },
    }
    # Note: file:///file2.py is missing from current_files -> DELETED / REMOVED

    delta = evaluate_delta(prev_manifest, current_files)

    assert delta["file:///file1.py"].state == DeltaState.UNCHANGED
    assert delta["file:///file3.py"].state == DeltaState.NEW
    assert delta["file:///file3.py"].reason == DeltaReason.CREATED
    assert delta["file:///file2.py"].state == DeltaState.DELETED
    assert delta["file:///file2.py"].reason == DeltaReason.REMOVED


def test_delta_evaluator_moved_file_detection():
    old_entry = ManifestEntry(
        document_id="1" * 64,
        revision_id="r1" + "0" * 62,
        source_uri="file:///old_path/main.py",
        content_hash="same_hash_123" + "0" * 51,
        state=DeltaState.UNCHANGED,
    )
    prev_manifest = VersionedManifest(entries={"file:///old_path/main.py": old_entry})

    # File moved from old_path/main.py -> new_path/main.py with identical content_hash
    current_files = {
        "file:///new_path/main.py": {
            "document_id": "1" * 64,
            "revision_id": "r1" + "0" * 62,
            "content_hash": "same_hash_123" + "0" * 51,
        },
    }

    delta = evaluate_delta(prev_manifest, current_files)

    assert "file:///new_path/main.py" in delta
    assert delta["file:///new_path/main.py"].state == DeltaState.MODIFIED
    assert delta["file:///new_path/main.py"].reason == DeltaReason.MOVED
