from __future__ import annotations

from md_generator.sap.markdown.chunking.chunk_strategy import (
    AuthorizationChunkStrategy,
    EntityChunkStrategy,
    LineageChunkStrategy,
    RelationshipChunkStrategy,
    SapChunkStrategy,
    ValidationChunkStrategy,
)

STRATEGIES: dict[str, SapChunkStrategy] = {
    EntityChunkStrategy.name: EntityChunkStrategy(),
    RelationshipChunkStrategy.name: RelationshipChunkStrategy(),
    ValidationChunkStrategy.name: ValidationChunkStrategy(),
    AuthorizationChunkStrategy.name: AuthorizationChunkStrategy(),
    LineageChunkStrategy.name: LineageChunkStrategy(),
}


def get_strategies(names: list[str]) -> list[SapChunkStrategy]:
    return [STRATEGIES[n] for n in names if n in STRATEGIES]
