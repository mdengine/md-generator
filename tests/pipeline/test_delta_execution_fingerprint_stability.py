from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from md_generator.pipeline.base import MDPipeline
from md_generator.pipeline.config import PipelineConfig


def test_delta_execution_fingerprint_stability():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        file_a = root / "sample.py"
        file_a.write_text("def fn():\n    pass\n", encoding="utf-8")

        # Run 1: NEW file processing
        pipeline1 = MDPipeline()
        res1 = pipeline1.process_directory(str(root))

        assert res1.statistics.processed_count == 1
        assert res1.statistics.unchanged_count == 0
        fp1 = res1.execution_fingerprint
        run_id1 = res1.run_id

        # Run 2: UNCHANGED file (delta sync enabled, extraction skipped)
        cfg2 = PipelineConfig(manifest=res1.manifest, enable_delta_sync=True)
        pipeline2 = MDPipeline(config=cfg2)
        res2 = pipeline2.process_directory(str(root))

        assert res2.statistics.processed_count == 0
        assert res2.statistics.unchanged_count == 1
        fp2 = res2.execution_fingerprint
        run_id2 = res2.run_id

        # Invariant 1: Physical execution IDs (run_id) MUST be unique per invocation
        assert run_id1 != run_id2

        # Invariant 2: Logical request & result execution fingerprint MUST be identical across runs
        assert fp1 == fp2
