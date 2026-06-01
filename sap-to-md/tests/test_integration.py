from __future__ import annotations

from pathlib import Path

from md_generator.sap.core.extractor import extract_to_markdown
from md_generator.sap.core.run_config import SapRunConfig

FIXTURES = Path(__file__).parent / "fixtures"


def test_extract_to_markdown_mini_repo(tmp_path: Path):
    out = tmp_path / "sap-md"
    cfg = SapRunConfig(
        input_paths=[FIXTURES],
        output_path=out,
        include=frozenset({"entities", "graphs", "json_output", "governance", "chunks", "odata_catalog"}),
    )
    cfg = cfg.normalized()
    from dataclasses import replace

    cfg = replace(
        cfg,
        chunking=replace(cfg.chunking, enabled=True),
        graph=replace(cfg.graph, enabled=True),
        analyzer=replace(cfg.analyzer, governance=True, lineage=True, relationships=True),
    )
    extract_to_markdown(cfg)
    assert (out / "README.md").is_file()
    assert (out / "export_manifest.json").is_file()
    assert (out / "entities").is_dir()
    assert (out / "odata" / "index.md").is_file()
    assert (out / "graph-full.json").is_file()
    assert (out / "chunks" / "index.json").is_file()
