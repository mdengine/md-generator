from __future__ import annotations

import pytest

from md_generator.db.api.schemas import DbToMdRunBody
from md_generator.db.core.models import ELASTICSEARCH_FEATURES, FEATURES, _LEGACY_FEATURES


def test_legacy_features_unchanged() -> None:
  expected_legacy = {
      "tables",
      "views",
      "indexes",
      "procedures",
      "functions",
      "triggers",
      "sequences",
      "partitions",
      "synonyms",
      "dependencies",
      "oracle_packages",
      "oracle_clusters",
      "mongodb_collections",
      "erd",
  }
  assert _LEGACY_FEATURES == expected_legacy
  assert expected_legacy <= FEATURES


def test_elasticsearch_features_are_additive() -> None:
  assert "elasticsearch_indices" in FEATURES
  assert "tables" in FEATURES
  assert ELASTICSEARCH_FEATURES.isdisjoint(_LEGACY_FEATURES)


def test_postgres_db_to_md_body_unchanged() -> None:
  body = DbToMdRunBody(
      database={"type": "postgres", "uri": "postgresql://u:p@localhost/db", "schema": "public"},
      features={"include": ["tables", "views", "indexes"]},
  )
  cfg = body.to_run_config()
  assert cfg.db_type == "postgres"
  assert cfg.effective_features() == frozenset({"tables", "views", "indexes"})


def test_unknown_feature_rejected() -> None:
  with pytest.raises(ValueError, match="Unknown features"):
      DbToMdRunBody(
          database={"type": "postgres", "uri": "postgresql://localhost/db"},
          features={"include": ["not_a_real_feature"]},
      )


def test_elasticsearch_features_validate() -> None:
  body = DbToMdRunBody(
      database={"type": "elasticsearch", "uri": "https://localhost:9200"},
      features={
          "include": [
              "elasticsearch_indices",
              "elasticsearch_data_streams",
              "elasticsearch_search_architecture",
          ]
      },
  )
  cfg = body.to_run_config()
  assert cfg.db_type == "elasticsearch"
  assert "elasticsearch_indices" in cfg.effective_features()


def test_elasticsearch_security_flags_are_valid_and_non_exporting(tmp_path) -> None:
  from pathlib import Path
  from unittest.mock import MagicMock

  from md_generator.db.core.elasticsearch_export import export_elasticsearch_markdown
  from md_generator.db.core.run_config import RunConfig

  for flag in (
      "elasticsearch_security_roles",
      "elasticsearch_security_users",
      "elasticsearch_security_api_keys",
  ):
      assert flag in FEATURES

  adapter = MagicMock()
  adapter.db_type = "elasticsearch"
  cfg = RunConfig(
      db_type="elasticsearch",
      uri="https://localhost:9200",
      output_path=Path(tmp_path) / "out",
      include=frozenset({"elasticsearch_security_users"}),
      write_manifest=False,
  )
  root = export_elasticsearch_markdown(cfg, adapter, cfg.effective_features(), cfg.output_path)
  users_doc = root / "elasticsearch" / "security" / "users.md"
  assert users_doc.is_file()
  text = users_doc.read_text(encoding="utf-8")
  assert "intentional non-export" in text
  adapter.get_security_users.assert_not_called()
