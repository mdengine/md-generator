"""Java language adapter for Tree-sitter AST queries and FQN resolution."""

from md_generator.semantic.chunkers.languages.base import BaseLanguageAdapter, LanguageCapability

JAVA_CAPABILITY = LanguageCapability(
    language="java",
    grammar_name="tree-sitter-java",
    grammar_version="0.21.0",
    supported_symbols=["class", "interface", "enum", "method", "constructor", "import"],
    supported_relationships=["DEFINES", "CALLS", "IMPORTS", "INHERITS", "IMPLEMENTS"],
    fqn_strategy="java_package_qualified",
    status="TIER_1",
)


class JavaLanguageAdapter(BaseLanguageAdapter):
    def __init__(self):
        super().__init__(JAVA_CAPABILITY)
