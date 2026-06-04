from __future__ import annotations

from pathlib import Path

import pytest

from md_generator.sap.core.run_config import SapRunConfig, PipelineSection
from md_generator.sap.core.run_context import RunContext
from md_generator.sap.orchestration.pipeline_v2 import run_pipeline_v2


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "hana"


@pytest.mark.skipif(not FIXTURE_DIR.is_dir(), reason="HANA fixtures missing")
def test_pipeline_v2_hana_integration(tmp_path: Path):
    cfg = SapRunConfig(
        input_paths=[FIXTURE_DIR],
        output_path=tmp_path / "out",
        pipeline=PipelineSection(version=2, canonical_json=True, artifact_graph=True, rule_engine=True),
    )
    ctx = RunContext(
        input_paths=cfg.input_paths,
        output_dir=cfg.output_path,
        config=cfg,
        started_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
    )
    run_pipeline_v2(ctx)
    assert (tmp_path / "out" / "graph" / "artifacts.json").is_file()
    canon_dir = tmp_path / "out" / "json" / "canonical"
    assert any(canon_dir.glob("*.json"))
    assert (tmp_path / "out" / "hana" / "calculation-views").is_dir()
