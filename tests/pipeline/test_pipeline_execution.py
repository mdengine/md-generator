from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from md_generator.pipeline.base import MDPipeline
from md_generator.pipeline.config import PipelineConfig


def test_process_file_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        fpath = Path(tmpdir) / "sample.py"
        fpath.write_text("def hello():\n    print('Hello World')\n", encoding="utf-8")

        pipeline = MDPipeline()
        result = pipeline.process_file(str(fpath))

        assert len(result.documents) == 1
        assert result.documents[0].sanitized_content.strip().startswith("``` python")
        assert result.statistics.processed_count == 1
        assert result.statistics.failed_count == 0
        assert len(result.errors) == 0
        assert result.manifest is not None


def test_process_directory_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "file1.py").write_text("x = 1\n", encoding="utf-8")
        (root / "file2.java").write_text("class Main {}\n", encoding="utf-8")

        pipeline = MDPipeline()
        result = pipeline.process_directory(str(root))

        assert len(result.documents) == 2
        assert result.statistics.total_discovered == 2
        assert result.statistics.processed_count == 2
        assert result.statistics.failed_count == 0


def test_process_file_forced_extraction_when_delta_disabled():
    with tempfile.TemporaryDirectory() as tmpdir:
        fpath = Path(tmpdir) / "test.txt"
        fpath.write_text("Sample content", encoding="utf-8")

        # First run to get initial manifest
        pipeline1 = MDPipeline()
        res1 = pipeline1.process_file(str(fpath))
        manifest1 = res1.manifest

        # Second run with enable_delta_sync=False
        cfg2 = PipelineConfig(enable_delta_sync=False, manifest=manifest1)
        pipeline2 = MDPipeline(config=cfg2)
        res2 = pipeline2.process_file(str(fpath))

        # Forced extraction re-runs processing
        assert res2.statistics.processed_count == 1
        assert res2.statistics.unchanged_count == 0
        assert len(res2.documents) == 1
