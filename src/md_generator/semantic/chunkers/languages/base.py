"""Base language capability and adapter specification.

Provides LanguageCapability and BaseLanguageAdapter protocols for language-specific
tree-sitter query mapping and FQN resolution.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from md_generator.semantic.chunkers.identity import SymbolIdentity, compute_fqn


@dataclass
class LanguageCapability:
    """Capability descriptor for a language grammar adapter."""
    language: str
    grammar_name: str
    grammar_version: str
    supported_symbols: List[str]
    supported_relationships: List[str]
    fqn_strategy: str
    parse_recovery: bool = True
    status: str = "TIER_1"                              # TIER_1 (Req), TIER_2, TIER_3


class BaseLanguageAdapter:
    """Base class for language-specific AST query mapping and FQN resolution."""

    def __init__(self, capability: LanguageCapability):
        self.capability = capability

    def resolve_identity(
        self,
        symbol_kind: str,
        local_name: str,
        parent_symbol: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> SymbolIdentity:
        """Resolve a language-aware SymbolIdentity."""
        return compute_fqn(
            language=self.capability.language,
            symbol_kind=symbol_kind,
            local_name=local_name,
            parent_symbol=parent_symbol,
            namespace=namespace,
        )
