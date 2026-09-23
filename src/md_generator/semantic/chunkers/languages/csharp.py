"""C# language adapter for Tree-sitter AST queries and FQN resolution."""

from md_generator.semantic.chunkers.languages.base import BaseLanguageAdapter, LanguageCapability

CSHARP_CAPABILITY = LanguageCapability(
    language="csharp",
    grammar_name="tree-sitter-c-sharp",
    grammar_version="0.21.0",
    supported_symbols=["class", "interface", "struct", "method", "namespace"],
    supported_relationships=["DEFINES", "CALLS", "INHERITS", "IMPLEMENTS"],
    fqn_strategy="csharp_namespace_qualified",
    status="TIER_2",
)


class CSharpLanguageAdapter(BaseLanguageAdapter):
    def __init__(self):
        super().__init__(CSHARP_CAPABILITY)
