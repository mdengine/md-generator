"""Go language adapter for Tree-sitter AST queries and FQN resolution."""

from md_generator.semantic.chunkers.languages.base import BaseLanguageAdapter, LanguageCapability

GO_CAPABILITY = LanguageCapability(
    language="go",
    grammar_name="tree-sitter-go",
    grammar_version="0.21.0",
    supported_symbols=["struct", "interface", "function", "method", "import"],
    supported_relationships=["DEFINES", "CALLS", "IMPORTS", "IMPLEMENTS"],
    fqn_strategy="go_package_qualified",
    status="TIER_1",
)


class GoLanguageAdapter(BaseLanguageAdapter):
    def __init__(self):
        super().__init__(GO_CAPABILITY)
