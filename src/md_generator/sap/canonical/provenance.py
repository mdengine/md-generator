from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class ProvenanceBundle(BaseModel):
    artifact_version: str = ""
    schema_version: str = "1.0.0"
    parser_version: str = ""
    parser_id: str = ""
    generator_versions: dict[str, str] = Field(default_factory=dict)
    run_id: str = ""
    parsed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_checksum: str = ""

    def to_manifest_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
