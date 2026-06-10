from __future__ import annotations

from pydantic import BaseModel, Field


class ArtifactIdentity(BaseModel):
    stable_id: str
    physical_id: str = ""
    semantic_id: str = ""
    runtime_id: str = ""
    display_id: str = ""
    namespace: str = ""
    aliases: list[str] = Field(default_factory=list)

    @classmethod
    def from_legacy(
        cls,
        *,
        stable_id: str,
        name: str,
        namespace: str = "",
        semantic_entity: str | None = None,
        aliases: list[str] | None = None,
    ) -> ArtifactIdentity:
        return cls(
            stable_id=stable_id,
            physical_id=name,
            semantic_id=semantic_entity or "",
            display_id=name,
            namespace=namespace,
            aliases=list(aliases or []),
        )
