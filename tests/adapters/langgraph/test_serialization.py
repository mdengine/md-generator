"""Tests for recursive checkpoint serialization and path reporting (P2A-R04)."""

import json
import math
import pytest
from langchain_core.documents import Document
from md_generator.adapters.langgraph.exceptions import GraphStateValidationError
from md_generator.adapters.langgraph.state import (
    validate_graph_state,
    validate_serializable_value,
)


def test_serialization_primitive_and_clean_collections():
    """Primitive values and clean collections validate without error."""
    clean_dict = {
        "str": "hello",
        "int": 42,
        "bool": True,
        "float": 3.14159,
        "none": None,
        "list": [1, "two", 3.0, False],
        "nested": {"key": "val", "arr": [None, 10]},
    }
    validate_serializable_value(clean_dict, "root")
    # Verify json.dumps round-trip with allow_nan=False
    dumped = json.dumps(clean_dict, allow_nan=False)
    assert json.loads(dumped)["int"] == 42


def test_serialization_nested_nan_path_reporting():
    """Nested dict -> list -> dict -> NaN reports exact dot/bracket path."""
    state = {
        "tenant_id": "tenant-A",
        "documents": [
            Document(page_content="0", metadata={"tenant_id": "tenant-A"}),
            Document(page_content="1", metadata={"tenant_id": "tenant-A"}),
            Document(
                page_content="2",
                metadata={
                    "tenant_id": "tenant-A",
                    "attributes": [
                        {"flag": 1},
                        {"score": float("nan")},
                    ],
                },
            ),
        ],
    }

    with pytest.raises(GraphStateValidationError) as exc_info:
        validate_graph_state(state, trusted_tenant="tenant-A")

    err_msg = str(exc_info.value)
    assert "documents[2].metadata.attributes[1].score" in err_msg
    assert "Non-finite float" in err_msg


def test_serialization_nested_object_path_reporting():
    """Nested dict -> list -> object() reports exact dot/bracket path."""
    state = {
        "tenant_id": "tenant-A",
        "documents": [
            Document(page_content="0", metadata={"tenant_id": "tenant-A"}),
            Document(page_content="1", metadata={"tenant_id": "tenant-A"}),
            Document(
                page_content="2",
                metadata={
                    "tenant_id": "tenant-A",
                    "attributes": [
                        {"flag": 1},
                        object(),
                    ],
                },
            ),
        ],
    }

    with pytest.raises(GraphStateValidationError) as exc_info:
        validate_graph_state(state, trusted_tenant="tenant-A")

    err_msg = str(exc_info.value)
    assert "documents[2].metadata.attributes[1]" in err_msg
    assert "Unsupported non-serializable object" in err_msg


def test_serialization_non_string_dict_keys():
    """Non-string dictionary keys must be rejected with path indicator."""
    bad_dict = {"valid": {100: "integer key"}}
    with pytest.raises(GraphStateValidationError, match=r"Dictionary keys must be strings at 'root\.valid'"):
        validate_serializable_value(bad_dict, "root")


def test_serialization_callable_rejected():
    """Callable functions/lambdas must be rejected."""
    bad_state = {
        "tenant_id": "tenant-A",
        "metadata": {"callback": lambda x: x},
    }
    with pytest.raises(GraphStateValidationError, match=r"Unsupported non-serializable object of type 'function' at 'metadata\.callback'"):
        validate_graph_state(bad_state, trusted_tenant="tenant-A")


def test_serialization_infinite_floats_rejected():
    """Positive and negative infinity must be rejected."""
    with pytest.raises(GraphStateValidationError, match="Non-finite float not permitted"):
        validate_serializable_value({"inf": float("inf")}, "state")

    with pytest.raises(GraphStateValidationError, match="Non-finite float not permitted"):
        validate_serializable_value({"neginf": float("-inf")}, "state")


def test_serialization_unknown_state_keys_validated():
    """Unknown state keys are preserved but strictly validated for serialization."""
    valid_custom_state = {
        "tenant_id": "tenant-A",
        "custom_audit_trail": {"step": 1, "duration_ms": 12.5},
    }
    assert validate_graph_state(valid_custom_state, trusted_tenant="tenant-A") == "tenant-A"

    invalid_custom_state = {
        "tenant_id": "tenant-A",
        "custom_audit_trail": {"socket": object()},
    }
    with pytest.raises(GraphStateValidationError, match=r"Unsupported non-serializable object.*custom_audit_trail\.socket"):
        validate_graph_state(invalid_custom_state, trusted_tenant="tenant-A")
