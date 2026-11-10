"""Strict Pydantic v2 input argument schemas for CrewAI tools."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

__all__ = ["MDSearchInput"]


class MDSearchInput(BaseModel):
    """Strict input argument schema for mdengine CrewAI search tool.
    
    Invariants:
        1. extra="forbid": Unknown fields (including agent-supplied tenant_id) are strictly rejected.
        2. strict=True: Rejects loose type coercions (e.g., int/float to string).
        3. frozen=True: Input instance is immutable.
        4. Option A: Retrieval uses the retriever's configured top_k setting without a conflicting per-call limit.
    """
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
    )

    query: str = Field(
        ...,
        description="Search query to locate relevant enterprise documentation, code, and architecture specifications.",
        min_length=1,
    )

    @field_validator("query")
    @classmethod
    def validate_non_whitespace_query(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("Query must be a string.")
        stripped = v.strip()
        if not stripped:
            raise ValueError("Query string cannot be empty or whitespace-only.")
        return stripped
