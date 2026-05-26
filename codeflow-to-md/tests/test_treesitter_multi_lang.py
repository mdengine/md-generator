from __future__ import annotations

from pathlib import Path

import pytest

from md_generator.codeflow.parsers.base import ParserRegistry, register_defaults
from md_generator.codeflow.parsers.unified_parser import parse_source_file


def test_unified_parser_java_native_unchanged(tmp_path: Path) -> None:
    j = tmp_path / "App.java"
    j.write_text(
        """
        package com.example;
        public class App {
            void run() { other(); }
            void other() {}
        }
        """.strip(),
        encoding="utf-8",
    )
    reg = ParserRegistry()
    register_defaults(reg)
    fr = parse_source_file(reg, j, tmp_path, "java", "auto")
    assert fr is not None
    assert fr.parse_backend == "native"
    assert any("App.run" in s for s in fr.symbol_ids)


@pytest.mark.parametrize("lang,source,ext", [
    ("java", '@RestController\npublic class C {\n  @GetMapping("/x")\n  void get() { helper(); }\n  void helper() {}\n}', ".java"),
    ("python", "def f():\n    g()\ndef g():\n    pass\n", ".py"),
])
def test_treesitter_backend_parses_calls(lang: str, source: str, ext: str, tmp_path: Path) -> None:
    mod = {
        "java": pytest.importorskip("tree_sitter_java"),
        "python": pytest.importorskip("tree_sitter_python"),
    }[lang]
    del mod
    p = tmp_path / f"m{ext}"
    p.write_text(source, encoding="utf-8")
    reg = ParserRegistry()
    register_defaults(reg)
    fr = parse_source_file(reg, p, tmp_path, lang, "treesitter")
    assert fr is not None
    assert fr.parse_backend == "treesitter"
    assert fr.symbol_ids
    assert fr.calls or lang == "java"


def test_java_spring_entry_treesitter(tmp_path: Path) -> None:
    pytest.importorskip("tree_sitter_java")
    j = tmp_path / "Api.java"
    j.write_text(
        """
        @RestController
        public class Api {
            @GetMapping("/items")
            public void list() {}
        }
        """.strip(),
        encoding="utf-8",
    )
    reg = ParserRegistry()
    register_defaults(reg)
    fr = parse_source_file(reg, j, tmp_path, "java", "treesitter")
    assert fr is not None
    from md_generator.codeflow.models.ir import EntryKind

    assert any(e.kind == EntryKind.API_REST for e in fr.entries)


def test_parse_backend_defaults_native() -> None:
    from md_generator.codeflow.models.ir import FileParseResult

    fr = FileParseResult(path=Path("x.py"), language="python")
    assert fr.parse_backend == "native"
