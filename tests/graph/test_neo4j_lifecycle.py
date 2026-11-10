from unittest.mock import MagicMock
import pytest

from md_generator.graph.stores.neo4j import Neo4jGraphStore


def test_neo4j_driver_mock_lifecycle():
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    # Mock health_check query result
    mock_result = MagicMock()
    mock_result.single.return_value = {"alive": 1}
    mock_session.run.return_value = mock_result

    store = Neo4jGraphStore(driver=mock_driver)
    store.initialize()

    # Health check invokes driver session
    assert store.health_check() is True
    assert mock_session.run.called

    # Close lifecycle
    store.close()
    # Note: store does not close injected driver if not owned
    assert store._driver is not None


def test_neo4j_context_manager():
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_result = MagicMock()
    mock_result.single.return_value = {"alive": 1}
    mock_session.run.return_value = mock_result

    with Neo4jGraphStore(driver=mock_driver) as store:
        assert store.health_check() is True
