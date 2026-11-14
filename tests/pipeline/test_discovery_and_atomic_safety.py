from __future__ import annotations

import os
from pathlib import Path
import pytest
from unittest.mock import patch

from md_generator.lineage.manifest import DeltaState, DeltaReason, ManifestEntry, VersionedManifest
from md_generator.pipeline.base import MDPipeline
from md_generator.pipeline.config import PipelineConfig
from md_generator.pipeline.registry import IngestionDiscoveryError


def test_missing_directory_raises_file_not_found():
    pipeline = MDPipeline()
    with pytest.raises(FileNotFoundError, match="Target directory does not exist"):
        pipeline.process_directory("/non/existent/path/for/sure/12345")


def test_file_given_to_process_directory_raises_not_a_directory(tmp_path: Path):
    regular_file = tmp_path / "regular.txt"
    regular_file.write_text("sample content")

    pipeline = MDPipeline()
    with pytest.raises(NotADirectoryError, match="Target path is not a directory"):
        pipeline.process_directory(str(regular_file))


def test_missing_file_given_to_process_file_raises_file_not_found():
    pipeline = MDPipeline()
    with pytest.raises(FileNotFoundError, match="Target file does not exist"):
        pipeline.process_file("/non/existent/file.txt")


def test_directory_given_to_process_file_raises_is_a_directory(tmp_path: Path):
    pipeline = MDPipeline()
    with pytest.raises(IsADirectoryError, match="Target is a directory"):
        pipeline.process_file(str(tmp_path))


def test_recursive_discovery_failure_aborts_without_tombstones(tmp_path: Path):
    root_dir = tmp_path / "corpus"
    root_dir.mkdir()
    f1 = root_dir / "valid.txt"
    f1.write_text("valid file")

    initial_manifest = VersionedManifest(
        config_fingerprint="cfg_init",
        tenant_id="default",
        entries={
            f1.resolve().as_uri(): ManifestEntry(
                document_id="doc1",
                revision_id="rev1",
                source_uri=f1.resolve().as_uri(),
                content_hash="hash1",
                state=DeltaState.UNCHANGED,
            )
        }
    )

    pipeline = MDPipeline(config=PipelineConfig(manifest=initial_manifest))

    # Simulate an OS / permission error during traversal
    def failing_walk(top, onerror=None):
        if onerror:
            onerror(PermissionError(13, "Permission denied", str(top)))
        raise IngestionDiscoveryError("Traversal failed")

    with patch("os.walk", side_effect=failing_walk):
        with pytest.raises(IngestionDiscoveryError):
            pipeline.process_directory(str(root_dir))

    # Verify initial manifest remains 100% untouched and no deletion tombstones were issued
    assert initial_manifest.entries[f1.resolve().as_uri()].state == DeltaState.UNCHANGED


def test_legitimate_empty_directory_deletes_manifest_entries(tmp_path: Path):
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()

    old_file_uri = "file:///old_file.txt"
    initial_manifest = VersionedManifest(
        config_fingerprint="cfg_init",
        tenant_id="default",
        entries={
            old_file_uri: ManifestEntry(
                document_id="doc1",
                revision_id="rev1",
                source_uri=old_file_uri,
                content_hash="hash1",
                state=DeltaState.UNCHANGED,
            )
        }
    )

    pipeline = MDPipeline(config=PipelineConfig(manifest=initial_manifest))
    res = pipeline.process_directory(str(empty_dir))

    assert res.statistics.deleted_count == 1
    assert old_file_uri in res.manifest.entries
    assert res.manifest.entries[old_file_uri].state == DeltaState.DELETED
    assert res.manifest.entries[old_file_uri].reason == DeltaReason.REMOVED


def test_atomic_manifest_persistence(tmp_path: Path):
    manifest = VersionedManifest(
        config_fingerprint="cfg_save",
        tenant_id="default",
        entries={}
    )
    target_file = tmp_path / "manifest.json"

    # Save atomically
    MDPipeline.save_manifest_atomically(manifest, target_file)
    assert target_file.exists()
    assert VersionedManifest.from_json(target_file.read_text(encoding="utf-8")).config_fingerprint == "cfg_save"

    # Test error during atomic write cleans up temp file
    with patch("os.replace", side_effect=OSError("Disk write error")):
        with pytest.raises(OSError):
            MDPipeline.save_manifest_atomically(manifest, target_file)

    # Temporary files should be cleaned up
    tmp_files = list(tmp_path.glob(".*.tmp.*"))
    assert len(tmp_files) == 0


def test_clean_orphaned_manifest_tmps(tmp_path: Path):
    stale_tmp = tmp_path / ".manifest.json.tmp.12345"
    stale_tmp.write_text("orphaned tmp")

    # Set old mtime (2 hours ago)
    old_time = os.time() if hasattr(os, "time") else 1000.0
    try:
        import time
        now = time.time()
        os.utime(stale_tmp, (now - 7200, now - 7200))
    except Exception:
        pass

    cleaned = MDPipeline.clean_orphaned_manifest_tmps(tmp_path, max_age_seconds=3600.0)
    assert cleaned == 1
    assert not stale_tmp.exists()

