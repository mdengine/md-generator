from __future__ import annotations

from md_generator.sap.markdown.chunking.chunk_strategy import (
    AuthorizationChunkStrategy,
    EntityChunkStrategy,
    LineageChunkStrategy,
    ODataCapabilitiesChunkStrategy,
    ODataEntitySetChunkStrategy,
    ODataIndexChunkStrategy,
    ODataServiceChunkStrategy,
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
    ODataEntitySetChunkStrategy.name: ODataEntitySetChunkStrategy(),
    ODataServiceChunkStrategy.name: ODataServiceChunkStrategy(),
    ODataIndexChunkStrategy.name: ODataIndexChunkStrategy(),
    ODataCapabilitiesChunkStrategy.name: ODataCapabilitiesChunkStrategy(),
}


def get_strategies(names: list[str]) -> list[SapChunkStrategy]:
    return [STRATEGIES[n] for n in names if n in STRATEGIES]
