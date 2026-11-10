"""TypeScript/JavaScript language adapter for Tree-sitter AST queries and FQN resolution."""

from md_generator.semantic.chunkers.languages.base import BaseLanguageAdapter, LanguageCapability

TYPESCRIPT_CAPABILITY = LanguageCapability(
    language="typescript",
    grammar_name="tree-sitter-typescript",
    grammar_version="0.21.0",
    supported_symbols=["class", "interface", "function", "method", "import"],
    supported_relationships=["DEFINES", "CALLS", "IMPORTS", "INHERITS", "IMPLEMENTS"],
    fqn_strategy="ts_module_export_qualified",
    status="TIER_1",
)


class TypeScriptLanguageAdapter(BaseLanguageAdapter):
    def __init__(self):
        super().__init__(TYPESCRIPT_CAPABILITY)
