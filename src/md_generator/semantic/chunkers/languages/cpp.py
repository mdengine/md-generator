"""C/C++ language adapter for Tree-sitter AST queries and FQN resolution."""

from md_generator.semantic.chunkers.languages.base import BaseLanguageAdapter, LanguageCapability

CPP_CAPABILITY = LanguageCapability(
    language="cpp",
    grammar_name="tree-sitter-cpp",
    grammar_version="0.21.0",
    supported_symbols=["class", "struct", "function", "method", "namespace"],
    supported_relationships=["DEFINES", "CALLS", "INHERITS"],
    fqn_strategy="cpp_namespace_qualified",
    status="TIER_2",
)


class CppLanguageAdapter(BaseLanguageAdapter):
    def __init__(self):
        super().__init__(CPP_CAPABILITY)
