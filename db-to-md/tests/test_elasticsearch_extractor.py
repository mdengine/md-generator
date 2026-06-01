from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from md_generator.db.core.extractor import extract_to_markdown
from md_generator.db.core.run_config import RunConfig


def test_extract_elasticsearch_writes_readme_only(tmp_path: Path) -> None:
    from md_generator.db.core.models import ElasticsearchIndexInfo

    adapter = MagicMock()
    adapter.db_type = "elasticsearch"
    adapter.validate_connection.return_value = None
    adapter.close.return_value = None
    adapter.cluster_name = "test-cluster"
    adapter.get_indices.return_value = [
        ElasticsearchIndexInfo(
            name="idx1",
            aliases=(),
            mappings={"properties": {"a": {"type": "keyword"}}},
            settings={},
            shard_config={},
        )
    ]
    adapter.get_alias_map.return_value = {}

    cfg = RunConfig(
        db_type="elasticsearch",
        uri="https://localhost:9200",
        output_path=tmp_path / "docs",
        include=frozenset({"elasticsearch_indices"}),
        limits={"index_pattern": "*"},
        write_manifest=False,
    )

    with patch("md_generator.db.core.extractor.create_adapter", return_value=adapter):
        out = extract_to_markdown(cfg)

    assert out == cfg.output_path.resolve()
    readme = out / "README.md"
    assert readme.is_file()
    text = readme.read_text(encoding="utf-8")
    assert "elasticsearch" in text
    assert "test-cluster" in text
    assert not (out / "tables").exists()
    assert (out / "elasticsearch" / "indices" / "idx1.md").is_file()
    adapter.validate_connection.assert_called_once()
    adapter.close.assert_called_once()


def test_extract_postgres_still_uses_sql_path(tmp_path: Path) -> None:
    """Elasticsearch branch must not run for postgres (regression)."""
    cfg = RunConfig(
        db_type="postgres",
        uri="postgresql://invalid:5432/nodb",
        schema="public",
        output_path=tmp_path / "docs",
        include=frozenset({"tables"}),
        write_manifest=False,
    )
    with patch("md_generator.db.core.extractor.create_adapter") as mock_create:
        adapter = MagicMock()
        adapter.db_type = "postgres"
        adapter.validate_connection.side_effect = RuntimeError("connection refused")
        mock_create.return_value = adapter
        try:
            extract_to_markdown(cfg)
        except RuntimeError as e:
            assert "connection" in str(e).lower()
        else:
            raise AssertionError("expected connection failure")
    mock_create.assert_called_once()
