"""Tests for SQL DDL database table and view chunker."""

import hashlib
from md_generator.semantic.chunkers.db import DBChunker
from md_generator.semantic.model.schema import CanonicalMetadata, SemanticDocument


def _make_doc_id(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def test_sql_ddl_table_chunking():
    chunker = DBChunker()
    sql_code = """
CREATE TABLE orders (
    id INT PRIMARY KEY,
    customer_id INT NOT NULL,
    total DECIMAL(10, 2)
);

CREATE VIEW active_orders AS
SELECT * FROM orders WHERE total > 0;
"""

    doc = SemanticDocument(
        document_id=_make_doc_id("doc-sql-1"),
        sanitized_content=sql_code,
        metadata=CanonicalMetadata(source_uri="file:///schema.sql", source_type="sql"),
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) == 2
    tables = [c.metadata.table_name for c in chunks if c.metadata]
    assert "orders" in tables
    assert "active_orders" in tables


def test_sql_symbol_extraction():
    chunker = DBChunker()
    sql_code = "CREATE TABLE users (id INT PRIMARY KEY);"

    doc = SemanticDocument(
        document_id=_make_doc_id("doc-sql-2"),
        sanitized_content=sql_code,
        metadata=CanonicalMetadata(source_uri="file:///users.sql", source_type="sql"),
    )

    res = chunker.extract_symbols(doc)
    assert len(res.entities) == 1
    assert res.entities[0].entity_type == "TABLE"
    assert res.entities[0].name == "users"
