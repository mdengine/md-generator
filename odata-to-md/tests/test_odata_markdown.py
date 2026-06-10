from __future__ import annotations

from pathlib import Path

from md_generator.odata.core.extractor import extract_to_markdown
from md_generator.odata.core.run_config import OdataRunConfig

FIXTURES = Path(__file__).parent / "fixtures" / "odata"


def test_odata_catalog_output(tmp_path: Path):
    out = tmp_path / "odata-md"
    cfg = OdataRunConfig(folder=FIXTURES, output_path=out).normalized()
    extract_to_markdown(cfg)
    index = (out / "odata" / "index.md").read_text(encoding="utf-8")
    assert (out / "odata" / "index.md").is_file()
    assert (out / "odata" / "services").is_dir()
    assert "# OData Service Catalog" in index
    assert "Entity set:" in index
    entity_sets = list((out / "odata" / "entity-sets").glob("*.md"))
    assert entity_sets
    es_md = entity_sets[0].read_text(encoding="utf-8")
    assert "## Supported Query Options" in es_md or "## CRUD capabilities" in es_md
