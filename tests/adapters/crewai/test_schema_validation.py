"""Tests for strict Pydantic v2 input schema validation (MDSearchInput)."""

import pytest
from pydantic import ValidationError

from md_generator.adapters.crewai.schema import MDSearchInput


def test_schema_valid_query_passes():
    """Valid non-empty query string passes schema validation."""
    model = MDSearchInput(query="enterprise search query")
    assert model.query == "enterprise search query"


def test_schema_query_whitespace_stripped():
    """Leading and trailing whitespace is stripped."""
    model = MDSearchInput(query="  trimmed query  ")
    assert model.query == "trimmed query"


@pytest.mark.parametrize("invalid_query", ["", "   ", "\t\n  ", "\n"])
def test_schema_rejects_empty_or_whitespace_query(invalid_query):
    """Empty or whitespace-only queries must raise ValidationError."""
    with pytest.raises(ValidationError):
        MDSearchInput(query=invalid_query)


@pytest.mark.parametrize("non_string_query", [123, 45.6, True, False, None, ["query"], {"q": "query"}])
def test_schema_rejects_non_string_query(non_string_query):
    """Strict validation must reject non-string queries without coercion."""
    with pytest.raises(ValidationError):
        MDSearchInput(query=non_string_query)


def test_schema_rejects_missing_query():
    """Missing query field must raise ValidationError."""
    with pytest.raises(ValidationError):
        MDSearchInput.model_validate({})


def test_schema_forbids_agent_supplied_tenant_id():
    """Unexpected tenant_id field must be strictly forbidden via extra='forbid'."""
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        MDSearchInput.model_validate({"query": "valid query", "tenant_id": "tenant-override"})


def test_schema_forbids_unexpected_limit_parameter():
    """Option A: limit is not accepted and must raise ValidationError via extra='forbid'."""
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        MDSearchInput.model_validate({"query": "valid query", "limit": 10})


def test_schema_forbids_arbitrary_extra_fields():
    """Any arbitrary extra field must raise ValidationError."""
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        MDSearchInput.model_validate({"query": "valid query", "filter_by": "tag", "debug": True})
