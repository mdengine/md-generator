"""Unit tests for Qdrant vector store adapter optional import behavior."""

import sys
import pytest
from unittest.mock import MagicMock

from md_generator.vector.exceptions import TenantBoundaryError, VectorStoreError
from md_generator.vector.model import CollectionConfig
from md_generator.vector.stores.qdrant import QdrantVectorStore


def test_qdrant_store_requires_tenant():
    mock_qdrant = MagicMock()
    sys.modules["qdrant_client"] = mock_qdrant
    try:
        store = QdrantVectorStore()
        store.initialize_collection(CollectionConfig())

        with pytest.raises(TenantBoundaryError):
            store.upsert_records([], tenant_id="")

        with pytest.raises(TenantBoundaryError):
            store.query(query_vector=[0.1, 0.2], top_k=2, tenant_id="")
    finally:
        to_del = [m for m in sys.modules if m == "qdrant_client" or m.startswith("qdrant_client.")]
        for m in to_del:
            del sys.modules[m]
