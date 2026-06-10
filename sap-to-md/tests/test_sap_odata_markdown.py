from __future__ import annotations

from pathlib import Path

from md_generator.sap.core.extractor import extract_to_markdown
from md_generator.sap.core.run_config import SapRunConfig

FIXTURES = Path(__file__).parent / "fixtures"


def test_sap_pipeline_odata_catalog(tmp_path: Path):
    out = tmp_path / "sap-md"
    cfg = SapRunConfig(
        input_paths=[FIXTURES],
        output_path=out,
        include=frozenset({"odata_catalog", "entities"}),
    ).normalized()
    extract_to_markdown(cfg)
    assert (out / "odata" / "index.md").is_file()
