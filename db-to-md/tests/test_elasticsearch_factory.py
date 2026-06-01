from __future__ import annotations

from md_generator.db.adapters.elasticsearch_adapter import ElasticsearchAdapter
from md_generator.db.adapters.factory import create_adapter


def test_create_adapter_elasticsearch() -> None:
    a = create_adapter("elasticsearch", "https://localhost:9200", limits={"index_pattern": "logs-*"})
    assert isinstance(a, ElasticsearchAdapter)
    assert a.db_type == "elasticsearch"
    a.close()


def test_create_adapter_es_alias() -> None:
    a = create_adapter("es", "http://127.0.0.1:9200", limits={})
    assert a.db_type == "elasticsearch"
    a.close()


def test_create_adapter_postgres_unchanged() -> None:
    a = create_adapter("postgres", "postgresql://u:p@localhost:5432/db", schema="public", limits={})
    assert a.db_type == "postgres"
    a.close()


def test_create_adapter_sqlite_unchanged() -> None:
    a = create_adapter("sqlite", "sqlite:///:memory:", schema="main", limits={})
    assert a.db_type == "sqlite"
    a.close()
