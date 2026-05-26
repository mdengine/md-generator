from __future__ import annotations

from pathlib import Path
from typing import Protocol

from md_generator.codeflow.models.ir import FileParseResult


class LanguageParser(Protocol):
    language: str

    def parse_file(self, path: Path, project_root: Path) -> FileParseResult:
        ...


class ParserRegistry:
    def __init__(self) -> None:
        self._by_lang: dict[str, LanguageParser] = {}

    def register(self, parser: LanguageParser) -> None:
        self._by_lang[parser.language] = parser

    def get(self, lang: str) -> LanguageParser | None:
        return self._by_lang.get(lang)

    def parse_file(self, path: Path, project_root: Path, lang: str) -> FileParseResult | None:
        p = self.get(lang)
        if not p:
            return None
        return p.parse_file(path, project_root)


def register_defaults(reg: ParserRegistry) -> None:
    from md_generator.codeflow.parsers.cpp_parser import CppParser
    from md_generator.codeflow.parsers.go_parser import GoParser
    from md_generator.codeflow.parsers.java_parser import JavaParser
    from md_generator.codeflow.parsers.php_parser import PhpParser
    from md_generator.codeflow.parsers.python_parser import PythonParser

    reg.register(PythonParser())
    reg.register(JavaParser())
    reg.register(CppParser())
    reg.register(GoParser())
    reg.register(PhpParser())
    try:
        from tree_sitter import Language

        import tree_sitter_javascript as tsjs
        import tree_sitter_typescript as tsts

        from md_generator.codeflow.parsers.treesitter_js_ts_parser import TreesitterJsTsParser

        reg.register(TreesitterJsTsParser("javascript", Language(tsjs.language())))
        reg.register(TreesitterJsTsParser("typescript", Language(tsts.language_typescript())))
        reg.register(TreesitterJsTsParser("tsx", Language(tsts.language_tsx())))
    except ImportError:
        pass
    try:
        from md_generator.codeflow.parsers.treesitter_csharp_parser import TreesitterCsharpParser
        from md_generator.codeflow.parsers.treesitter_kotlin_parser import TreesitterKotlinParser
        from md_generator.codeflow.parsers.treesitter_rust_parser import TreesitterRustParser

        reg.register(TreesitterRustParser())
        reg.register(TreesitterKotlinParser())
        reg.register(TreesitterCsharpParser())
    except ImportError:
        pass
    try:
        from md_generator.codeflow.parsers.treesitter_lua_parser import TreesitterLuaParser
        from md_generator.codeflow.parsers.treesitter_ruby_parser import TreesitterRubyParser
        from md_generator.codeflow.parsers.treesitter_swift_parser import TreesitterSwiftParser

        reg.register(TreesitterSwiftParser())
        reg.register(TreesitterRubyParser())
        reg.register(TreesitterLuaParser())
    except ImportError:
        pass
    try:
        from md_generator.codeflow.parsers.treesitter_scala_parser import TreesitterScalaParser
        from md_generator.codeflow.parsers.treesitter_zig_parser import TreesitterZigParser

        reg.register(TreesitterScalaParser())
        reg.register(TreesitterZigParser())
    except ImportError:
        pass
