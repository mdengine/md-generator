"""Language adapters and capability metadata package for tree-sitter AST chunking."""

from md_generator.semantic.chunkers.languages.base import BaseLanguageAdapter, LanguageCapability
from md_generator.semantic.chunkers.languages.python import PythonLanguageAdapter, PYTHON_CAPABILITY
from md_generator.semantic.chunkers.languages.java import JavaLanguageAdapter, JAVA_CAPABILITY
from md_generator.semantic.chunkers.languages.typescript import TypeScriptLanguageAdapter, TYPESCRIPT_CAPABILITY
from md_generator.semantic.chunkers.languages.go import GoLanguageAdapter, GO_CAPABILITY
from md_generator.semantic.chunkers.languages.cpp import CppLanguageAdapter, CPP_CAPABILITY
from md_generator.semantic.chunkers.languages.csharp import CSharpLanguageAdapter, CSHARP_CAPABILITY

__all__ = [
    "BaseLanguageAdapter",
    "LanguageCapability",
    "PythonLanguageAdapter",
    "PYTHON_CAPABILITY",
    "JavaLanguageAdapter",
    "JAVA_CAPABILITY",
    "TypeScriptLanguageAdapter",
    "TYPESCRIPT_CAPABILITY",
    "GoLanguageAdapter",
    "GO_CAPABILITY",
    "CppLanguageAdapter",
    "CPP_CAPABILITY",
    "CSharpLanguageAdapter",
    "CSHARP_CAPABILITY",
]
