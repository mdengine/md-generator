from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path

from md_generator.db.adapters.elasticsearch_json_adapter import ElasticsearchJsonAdapter
from md_generator.db.core.elasticsearch_bundle import extract_zip_bundle, is_elasticsearch_bundle_dir


def test_json_adapter_reads_mappings_and_settings(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    (bundle / "mappings").mkdir(parents=True)
    (bundle / "settings").mkdir(parents=True)
    (bundle / "mappings" / "idx1.json").write_text(
        json.dumps({"properties": {"a": {"type": "keyword"}}}),
        encoding="utf-8",
    )
    (bundle / "settings" / "idx1.json").write_text(
        json.dumps({"index": {"number_of_shards": "1"}}),
        encoding="utf-8",
    )
    adapter = ElasticsearchJsonAdapter(bundle, {})
    adapter.validate_connection()
    indices = adapter.get_indices()
    assert len(indices) == 1
    assert indices[0].name == "idx1"
    assert indices[0].mappings.get("properties")


def test_extract_zip_bundle(tmp_path: Path) -> None:
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "mappings/x.json",
            json.dumps({"properties": {"f": {"type": "text"}}}),
        )
    root = extract_zip_bundle(buf.getvalue(), tmp_path / "out")
    assert is_elasticsearch_bundle_dir(root)


def test_json_adapter_pipelines(tmp_path: Path) -> None:
    bundle = tmp_path / "b"
    (bundle / "pipelines").mkdir(parents=True)
    (bundle / "pipelines" / "p1.json").write_text(
        json.dumps({"processors": []}),
        encoding="utf-8",
    )
    adapter = ElasticsearchJsonAdapter(bundle, {})
    assert len(adapter.get_ingest_pipelines()) == 1
