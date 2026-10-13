import pytest

from md_generator.graph.exceptions import GraphQueryError
from md_generator.graph.model import RelationEdge, RELATIONSHIP_TYPE_REGEX
from md_generator.graph.stores.neo4j import Neo4jGraphStore


def test_relationship_type_regex_safety():
    valid_types = ["CALLS", "CONTAINS_CHUNK", "EXTENDS_1", "_PRIVATE_REL", "DEPENDS_ON"]
    for vt in valid_types:
        assert RELATIONSHIP_TYPE_REGEX.fullmatch(vt) is not None

    invalid_types = [
        "CALLS; DROP TABLE",
        "CALLS--comment",
        "CALLS'",
        'CALLS"',
        "CALLS/REL",
        "123_INVALID",
        "HAS-CHILD",
        "CALLS()",
    ]
    for it in invalid_types:
        assert RELATIONSHIP_TYPE_REGEX.fullmatch(it) is None


def test_neo4j_rejection_of_injected_relationship_types():
    # Construct store with mock or in-memory fallback
    store = Neo4jGraphStore(fallback_to_memory=True)

    bad_edge = RelationEdge.__new__(RelationEdge)
    # Bypass post_init to simulate corrupted instance
    bad_edge.edge_id = "e-bad"
    bad_edge.tenant_id = "tenant-1"
    bad_edge.source_id = "s"
    bad_edge.target_id = "t"
    bad_edge.relationship_type = "CALLS; DETACH DELETE n"
    bad_edge.weight = 1.0
    bad_edge.document_ids = []
    bad_edge.chunk_ids = []
    bad_edge.provenance = []
    bad_edge.properties = {}

    with pytest.raises(Exception):
        store.upsert_edges([bad_edge], tenant_id="tenant-1")


def test_neo4j_store_does_not_expose_raw_cypher_api():
    store = Neo4jGraphStore(fallback_to_memory=True)
    assert not hasattr(store, "execute_cypher")
    assert not hasattr(store, "run_cypher")
    assert not hasattr(store, "raw_query")


def test_neo4j_directional_traversal_semantics():
    """Verifies Neo4j directional traversal generates exact arrow patterns for in, out, both."""
    from unittest.mock import MagicMock

    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_res = MagicMock()
    mock_res.single.return_value = None
    mock_res.__iter__.return_value = []
    mock_session.run.return_value = mock_res

    store = Neo4jGraphStore(driver=mock_driver)
    tenant = "tenant-dir"

    # 1. get_neighbors: direction="out" -> ->(nbr:EntityNode)
    store.get_neighbors("n-center", tenant_id=tenant, direction="out")
    q_out = mock_session.run.call_args[0][0]
    kwargs_out = mock_session.run.call_args[1]
    assert "(n)-[r]->(nbr:EntityNode)" in q_out
    assert kwargs_out["tenant_id"] == tenant
    assert kwargs_out["node_id"] == "n-center"

    # 2. get_neighbors: direction="in" -> <-(nbr:EntityNode)
    store.get_neighbors("n-center", tenant_id=tenant, direction="in")
    q_in = mock_session.run.call_args[0][0]
    assert "(n)<-[r]-(nbr:EntityNode)" in q_in

    # 3. get_neighbors: direction="both" -> -(nbr:EntityNode)
    store.get_neighbors("n-center", tenant_id=tenant, direction="both")
    q_both = mock_session.run.call_args[0][0]
    assert "(n)-[r]-(nbr:EntityNode)" in q_both

    # 4. traverse: direction="out" -> -[*0..2]->(m:EntityNode)
    store.traverse(["n-center"], tenant_id=tenant, direction="out", max_depth=2)
    t_out = mock_session.run.call_args[0][0]
    assert "(s)-[r*0..2]->(m:EntityNode)" in t_out

    # 5. traverse: direction="in" -> <-[*0..2]-(m:EntityNode)
    store.traverse(["n-center"], tenant_id=tenant, direction="in", max_depth=2)
    t_in = mock_session.run.call_args[0][0]
    assert "(s)<-[r*0..2]-(m:EntityNode)" in t_in

    # 6. traverse: direction="both" -> -[*0..2]-(m:EntityNode)
    store.traverse(["n-center"], tenant_id=tenant, direction="both", max_depth=2)
    t_both = mock_session.run.call_args[0][0]
    assert "(s)-[r*0..2]-(m:EntityNode)" in t_both

    # 7. Invalid direction raises GraphQueryError
    with pytest.raises(GraphQueryError):
        store.get_neighbors("n-center", tenant_id=tenant, direction="invalid_dir")  # type: ignore
    with pytest.raises(GraphQueryError):
        store.traverse(["n-center"], tenant_id=tenant, direction="invalid_dir")  # type: ignore

