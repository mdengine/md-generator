from __future__ import annotations

from pathlib import Path

from md_generator.odata.core.extractor import extract_to_markdown
from md_generator.odata.core.run_config import OdataRunConfig

FIXTURES = Path(__file__).parent / "fixtures" / "odata"


def test_standalone_folder_pipeline(tmp_path: Path):
    out = tmp_path / "out"
    cfg = OdataRunConfig(
        folder=FIXTURES,
        output_path=out,
    ).normalized()
    from dataclasses import replace

    cfg = replace(cfg, features=replace(cfg.features, graph=True, chunks=True))
    extract_to_markdown(cfg)
    assert (out / "odata" / "index.md").is_file()
    assert (out / "graph-full.json").is_file()
    assert (out / "chunks" / "index.json").is_file()
    assert (out / "export_manifest.json").is_file()
