from __future__ import annotations

from datetime import datetime, timezone

from md_generator.sap.core.run_config import SapRunConfig
from md_generator.sap.core.run_context import RunContext
from md_generator.sap.orchestration.pipeline import run_pipeline


def extract_to_markdown(cfg: SapRunConfig) -> None:
    cfg = cfg.normalized()
    ctx = RunContext(
        input_paths=cfg.resolved_input_paths(),
        output_dir=cfg.output_path,
        config=cfg,
        started_at=datetime.now(timezone.utc),
    )
    run_pipeline(ctx)
