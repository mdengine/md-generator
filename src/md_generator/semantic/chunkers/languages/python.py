"""Python language adapter for Tree-sitter AST queries and FQN resolution."""

from md_generator.semantic.chunkers.languages.base import BaseLanguageAdapter, LanguageCapability

PYTHON_CAPABILITY = LanguageCapability(
    language="python",
    grammar_name="tree-sitter-python",
    grammar_version="0.21.0",
    supported_symbols=["class", "function", "method", "import"],
    supported_relationships=["DEFINES", "CALLS", "IMPORTS", "INHERITS"],
    fqn_strategy="python_module_qualified",
    status="TIER_1",
)


class PythonLanguageAdapter(BaseLanguageAdapter):
    def __init__(self):
        super().__init__(PYTHON_CAPABILITY)
