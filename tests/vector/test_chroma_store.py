"""Unit tests for ChromaDB vector store adapter optional import behavior."""

import sys
import pytest
from unittest.mock import MagicMock

from md_generator.vector.exceptions import TenantBoundaryError, VectorStoreError
from md_generator.vector.model import CollectionConfig
from md_generator.vector.stores.chroma import ChromaVectorStore


def test_chroma_store_requires_tenant():
    mock_chroma = MagicMock()
    sys.modules["chromadb"] = mock_chroma
    try:
        store = ChromaVectorStore()
        store.initialize_collection(CollectionConfig())

        with pytest.raises(TenantBoundaryError):
            store.upsert_records([], tenant_id="")

        with pytest.raises(TenantBoundaryError):
            store.query(query_vector=[0.1, 0.2], top_k=2, tenant_id="")
    finally:
        to_del = [m for m in sys.modules if m == "chromadb" or m.startswith("chromadb.")]
        for m in to_del:
            del sys.modules[m]
