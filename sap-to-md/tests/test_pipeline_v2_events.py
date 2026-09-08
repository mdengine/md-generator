from __future__ import annotations

import datetime
from pathlib import Path
from md_generator.sap.core.run_config import SapRunConfig, PipelineSection
from md_generator.sap.core.run_context import RunContext
from md_generator.sap.orchestration.pipeline_v2 import run_pipeline_v2


def test_pipeline_v2_events(tmp_path: Path):
    # Write a real CDS file to parse so discovery and legacy parsing find it
    cds_file = tmp_path / "zi_customer.ddls"
    cds_file.write_text(
        """
@AbapCatalog.sqlViewName: 'ZICUSTOMER'
define view ZI_Customer as select from kna1 as Customer
{
  key Customer.kunnr,
      Customer.name1
}
""",
        encoding="utf-8",
    )

    cfg = SapRunConfig(
        input_paths=[tmp_path],
        output_path=tmp_path / "out",
        pipeline=PipelineSection(
            version=2,
            canonical_json=True,
            artifact_graph=True,
            rule_engine=False,
            event_bus=True,
            cross_lineage=True,
        ),
    )
    ctx = RunContext(
        input_paths=cfg.input_paths,
        output_dir=cfg.output_path,
        config=cfg,
        started_at=datetime.datetime.now(datetime.timezone.utc),
    )
    run_pipeline_v2(ctx)
    assert ctx.event_bus is not None
    events = ctx.event_bus.events
    assert len(events) >= 3  # ArtifactParsedEvent, GraphMergedEvent, LineageResolvedEvent

    from md_generator.sap.framework.events import (
        ArtifactParsedEvent,
        GraphMergedEvent,
        LineageResolvedEvent,
    )

    parsed_events = [e for e in events if isinstance(e, ArtifactParsedEvent)]
    assert len(parsed_events) >= 1
    # Check stable_id format from normalizer/registry.py (which uses obj.object_id)
    # _identity_for(obj, "CDS::") prepends CDS:: to obj.object_id
    assert any("ZI_CUSTOMER" in e.artifact_id for e in parsed_events)
    assert any(e.artifact_type == "cds.view" for e in parsed_events)

    merged_events = [e for e in events if isinstance(e, GraphMergedEvent)]
    assert len(merged_events) == 1
    assert merged_events[0].graph_id == "run"
    assert merged_events[0].node_count > 0

    resolved_events = [e for e in events if isinstance(e, LineageResolvedEvent)]
    assert len(resolved_events) == 1
