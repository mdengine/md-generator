from __future__ import annotations

import datetime
from pathlib import Path
from md_generator.sap.core.run_config import SapRunConfig, PipelineSection
from md_generator.sap.core.run_context import RunContext
from md_generator.sap.orchestration.pipeline_v2 import run_pipeline_v2

BW_FIXTURES_DIR = Path(__file__).parent / "fixtures" / "bw" / "synthetic"
DS_FIXTURES_DIR = Path(__file__).parent / "fixtures" / "datasphere" / "synthetic"


def test_pipeline_v2_bw_ds_integration(tmp_path: Path):
    cfg = SapRunConfig(
        input_paths=[BW_FIXTURES_DIR, DS_FIXTURES_DIR],
        output_path=tmp_path / "out",
        pipeline=PipelineSection(
            version=2,
            canonical_json=True,
            artifact_graph=True,
            rule_engine=True,
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

    # 1. Verify that output files are generated
    out_dir = tmp_path / "out"

    # BW files
    assert (out_dir / "bw" / "adso" / "adso_sales.md").is_file()
    assert (out_dir / "bw" / "composite-provider" / "cp_sales.md").is_file()
    assert (out_dir / "bw" / "transformation" / "tr_sales.md").is_file()
    assert (out_dir / "bw" / "info-object" / "io_sales.md").is_file()
    assert (out_dir / "bw" / "dtp" / "dtp_sales.md").is_file()

    # Datasphere files
    assert (out_dir / "datasphere" / "analytical-model" / "am_sales.md").is_file()
    assert (out_dir / "datasphere" / "data-flow" / "df_sales.md").is_file()
    assert (out_dir / "datasphere" / "view" / "view_sales.md").is_file()

    # 2. Check rule engine findings
    # Read the canonical json to verify rule_findings metadata
    import json
    
    # ADSO missing key check
    adso_json = out_dir / "json" / "canonical" / "BW__ADSO__ADSO_SALES.json"
    assert adso_json.is_file()
    adso_data = json.loads(adso_json.read_text(encoding="utf-8"))
    findings = adso_data.get("metadata", {}).get("rule_findings", [])
    assert any(f["rule_id"] == "bw-adso-missing-key" for f in findings)

    # DTP no filter check
    dtp_json = out_dir / "json" / "canonical" / "BW__DTP__DTP_SALES.json"
    assert dtp_json.is_file()
    dtp_data = json.loads(dtp_json.read_text(encoding="utf-8"))
    findings = dtp_data.get("metadata", {}).get("rule_findings", [])
    assert any(f["rule_id"] == "bw-dtp-no-filter" for f in findings)

    # Data Flow no target check
    df_json = out_dir / "json" / "canonical" / "DATASPHERE__DF__DF_SALES.json"
    assert df_json.is_file()
    df_data = json.loads(df_json.read_text(encoding="utf-8"))
    findings = df_data.get("metadata", {}).get("rule_findings", [])
    assert any(f["rule_id"] == "datasphere-dataflow-no-target" for f in findings)
