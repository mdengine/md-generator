from __future__ import annotations

from pydantic import BaseModel, Field


class SemanticChunkSpec(BaseModel):
    chunk_id: str
    chunk_type: str
    artifact_type: str
    artifact_id: str
    semantic_id: str | None = None
    section: str = ""
    semantic_tags: list[str] = Field(default_factory=list)
    graph_refs: list[str] = Field(default_factory=list)
    content: str
    embedding_hint: str | None = None

    def to_jsonl_record(self) -> dict:
        return self.model_dump(mode="json")
