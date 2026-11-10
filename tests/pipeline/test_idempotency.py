from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from md_generator.lineage.ids import normalize_source_uri
from md_generator.pipeline.base import MDPipeline
from md_generator.pipeline.config import PipelineConfig


def test_reexecution_delta_sync_unchanged():
    with tempfile.TemporaryDirectory() as tmpdir:
        fpath = Path(tmpdir) / "sample.py"
        fpath.write_text("print('hello')", encoding="utf-8")

        # Initial execution
        pipeline1 = MDPipeline()
        res1 = pipeline1.process_file(str(fpath))
        assert res1.statistics.processed_count == 1
        assert res1.statistics.unchanged_count == 0

        # Second execution with previous manifest
        cfg2 = PipelineConfig(manifest=res1.manifest, enable_delta_sync=True)
        pipeline2 = MDPipeline(config=cfg2)
        res2 = pipeline2.process_file(str(fpath))

        assert res2.statistics.processed_count == 0
        assert res2.statistics.unchanged_count == 1
        assert len(res2.documents) == 0  # Bypassed conversion


def test_directory_deleted_tombstone_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        file_a = root / "a.py"
        file_b = root / "b.py"

        file_a.write_text("a = 1", encoding="utf-8")
        file_b.write_text("b = 2", encoding="utf-8")

        # Execution 1 with files a and b
        pipeline1 = MDPipeline()
        res1 = pipeline1.process_directory(str(root))
        assert res1.statistics.total_discovered == 2

        # Delete file_b
        file_b.unlink()

        # Execution 2 with file_b deleted
        cfg2 = PipelineConfig(manifest=res1.manifest)
        pipeline2 = MDPipeline(config=cfg2)
        res2 = pipeline2.process_directory(str(root))

        assert res2.statistics.total_discovered == 1
        assert res2.statistics.deleted_count == 1
        assert res2.statistics.unchanged_count == 1

        # Assert tombstone recorded in output manifest
        b_entries = [v for k, v in res2.manifest.entries.items() if k.endswith("b.py")]
        assert len(b_entries) == 1
        assert b_entries[0].state.value == "DELETED"
