from unittest.mock import MagicMock
import pytest

from md_generator.graph.exceptions import GraphStoreError
from md_generator.graph.model import EntityNode, RelationEdge
from md_generator.graph.stores.neo4j import Neo4jGraphStore


def test_neo4j_idempotent_merge_upsert():
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    mock_res = MagicMock()
    mock_res.single.return_value = {"cnt": 1}
    mock_session.run.return_value = mock_res

    store = Neo4jGraphStore(driver=mock_driver)
    node = EntityNode(
        node_id="n-1", tenant_id="t1", entity_id="e1", entity_type="class", name="A", qualified_name="a.A"
    )

    count = store.upsert_nodes([node], tenant_id="t1")
    assert count == 1

    # Verify Cypher query contains MERGE
    call_args = mock_session.run.call_args
    query = call_args[0][0]
    kwargs = call_args[1]

    assert "MERGE (n:EntityNode" in query
    assert kwargs["tenant_id"] == "t1"
    assert len(kwargs["batch"]) == 1
    assert kwargs["batch"][0]["node_id"] == "n-1"


def test_neo4j_transaction_delete_by_document():
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_tx = MagicMock()

    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_session.begin_transaction.return_value.__enter__.return_value = mock_tx

    res1 = MagicMock()
    res1.single.return_value = {"d_chunks": ["c1"], "purged_chunks": 1}
    res2 = MagicMock()
    res2.single.return_value = {"purged_docs": 1}
    res3 = MagicMock()
    res3.single.return_value = {"orphaned_entities": 1}
    res4 = MagicMock()
    res4.single.return_value = {"orphaned_edges": 1}

    mock_tx.run.side_effect = [res1, res2, res3, res4]

    store = Neo4jGraphStore(driver=mock_driver)
    purged = store.delete_by_document("doc-1", tenant_id="t1")

    assert purged == 4
    assert mock_tx.commit.called


def test_neo4j_transaction_rollback_on_error():
    """Explicitly verifies transaction rollback when reconciliation encounters an error."""
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_tx = MagicMock()

    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_session.begin_transaction.return_value.__enter__.return_value = mock_tx

    res1 = MagicMock()
    res1.single.return_value = {"d_chunks": ["c1"], "purged_chunks": 1}
    # Simulate database error on step 2
    mock_tx.run.side_effect = [res1, RuntimeError("Neo4j node lock conflict or query failure")]

    store = Neo4jGraphStore(driver=mock_driver)
    with pytest.raises(GraphStoreError) as exc_info:
        store.delete_by_document("doc-1", tenant_id="t1")

    assert "Error executing document reconciliation in Neo4j" in str(exc_info.value)
    # Rollback must be explicitly executed
    assert mock_tx.rollback.called
    # Commit must NEVER be called
    assert not mock_tx.commit.called


def test_neo4j_delete_by_tenant_scoping():
    """Verifies delete_by_tenant executes parameterized tenant-scoped Cypher query."""
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    mock_res = MagicMock()
    mock_res.single.return_value = {"cnt": 7}
    mock_session.run.return_value = mock_res

    store = Neo4jGraphStore(driver=mock_driver)
    deleted = store.delete_by_tenant("tenant-corp")

    assert deleted == 7
    call_args = mock_session.run.call_args
    query = call_args[0][0]
    kwargs = call_args[1]

    assert "MATCH (n:EntityNode {tenant_id: $tenant_id})" in query
    assert "DETACH DELETE" in query
    assert kwargs["tenant_id"] == "tenant-corp"

