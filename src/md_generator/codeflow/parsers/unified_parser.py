"""Single entry for per-file parsing with optional backend mode (native vs Tree-sitter)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

from md_generator.codeflow.models.ir import FileParseResult
from md_generator.codeflow.parsers.base import ParserRegistry
from md_generator.codeflow.parsers.cpp_parser import CppParser

ParserMode = Literal["auto", "treesitter", "external"]

logger = logging.getLogger(__name__)

_TREESITTER_LANGS = frozenset({"java", "python", "go", "php", "rust", "kotlin", "csharp"})


def _parse_treesitter_lang(lang: str, path: Path, project_root: Path) -> FileParseResult | None:
    try:
        if lang == "java":
            from md_generator.codeflow.parsers.treesitter_java_parser import TreesitterJavaParser

            return TreesitterJavaParser().parse_file(path, project_root)
        if lang == "python":
            from md_generator.codeflow.parsers.treesitter_python_parser import TreesitterPythonParser

            return TreesitterPythonParser().parse_file(path, project_root)
        if lang == "go":
            from md_generator.codeflow.parsers.treesitter_go_parser import TreesitterGoParser

            return TreesitterGoParser().parse_file(path, project_root)
        if lang == "php":
            from md_generator.codeflow.parsers.treesitter_php_parser import TreesitterPhpParser

            return TreesitterPhpParser().parse_file(path, project_root)
        if lang == "rust":
            from md_generator.codeflow.parsers.treesitter_rust_parser import TreesitterRustParser

            return TreesitterRustParser().parse_file(path, project_root)
        if lang == "kotlin":
            from md_generator.codeflow.parsers.treesitter_kotlin_parser import TreesitterKotlinParser

            return TreesitterKotlinParser().parse_file(path, project_root)
        if lang == "csharp":
            from md_generator.codeflow.parsers.treesitter_csharp_parser import TreesitterCsharpParser

            return TreesitterCsharpParser().parse_file(path, project_root)
    except ImportError as e:
        logger.debug("tree-sitter backend unavailable for %s: %s", lang, e)
    return None


def parse_source_file(
    reg: ParserRegistry,
    path: Path,
    project_root: Path,
    lang: str,
    mode: ParserMode,
) -> FileParseResult | None:
    """Dispatch to registry or language-specific Tree-sitter / C++ backends."""
    if mode == "external":
        if lang == "cpp":
            return CppParser().parse_clang_only(path, project_root)
        mode = "auto"

    if mode == "treesitter":
        if lang == "cpp":
            return CppParser().parse_treesitter_only(path, project_root)
        if lang in _TREESITTER_LANGS:
            fr = _parse_treesitter_lang(lang, path, project_root)
            if fr is not None:
                if fr.symbol_ids or fr.calls or fr.entries or fr.parse_backend == "treesitter":
                    return fr
                logger.warning(
                    "tree-sitter parse produced no symbols for %s (%s); grammar may be missing",
                    path,
                    lang,
                )
                return fr
        return reg.parse_file(path, project_root, lang)

    return reg.parse_file(path, project_root, lang)
