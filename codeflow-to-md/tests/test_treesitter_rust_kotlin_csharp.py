from __future__ import annotations

from pathlib import Path

import pytest

from md_generator.codeflow.lang_dispatch import lang_for_path
from md_generator.codeflow.models.ir import EntryKind
from md_generator.codeflow.parsers.base import ParserRegistry, register_defaults
from md_generator.codeflow.parsers.ir_enrich import enrich_parse_results_with_ir
from md_generator.codeflow.parsers.unified_parser import parse_source_file
from md_generator.codeflow.core.run_config import ScanConfig


@pytest.mark.parametrize(
    "lang,source,ext,import_mod",
    [
        (
            "rust",
            "struct S;\nimpl S {\n fn run(&self) { helper(); }\n}\nfn helper() {}\n",
            ".rs",
            "tree_sitter_rust",
        ),
        (
            "kotlin",
            "package test\nclass App {\n fun run() { helper() }\n}\nfun helper() {}\n",
            ".kt",
            "tree_sitter_kotlin",
        ),
        (
            "csharp",
            "class App {\n public void Run() { Helper(); }\n}\nclass Helper { public void H() {} }\n",
            ".cs",
            "tree_sitter_c_sharp",
        ),
    ],
)
def test_treesitter_auto_and_mode(lang: str, source: str, ext: str, import_mod: str, tmp_path: Path) -> None:
    pytest.importorskip(import_mod)
    p = tmp_path / f"m{ext}"
    p.write_text(source, encoding="utf-8")
    reg = ParserRegistry()
    register_defaults(reg)
    for mode in ("auto", "treesitter"):
        fr = parse_source_file(reg, p, tmp_path, lang, mode)
        assert fr is not None
        assert fr.parse_backend == "treesitter"
        assert fr.symbol_ids
        assert fr.calls


def test_rust_symbol_id_format(tmp_path: Path) -> None:
    pytest.importorskip("tree_sitter_rust")
    p = tmp_path / "lib.rs"
    p.write_text("fn top() {}\n", encoding="utf-8")
    reg = ParserRegistry()
    register_defaults(reg)
    fr = parse_source_file(reg, p, tmp_path, "rust", "auto")
    assert fr is not None
    assert any(s.endswith("::top") and "lib.rs::" in s for s in fr.symbol_ids)


def test_kotlin_spring_entry_treesitter(tmp_path: Path) -> None:
    pytest.importorskip("tree_sitter_kotlin")
    k = tmp_path / "Api.kt"
    k.write_text(
        """
        @RestController
        class Api {
            @GetMapping("/items")
            fun list() {}
        }
        """.strip(),
        encoding="utf-8",
    )
    reg = ParserRegistry()
    register_defaults(reg)
    fr = parse_source_file(reg, k, tmp_path, "kotlin", "auto")
    assert fr is not None
    assert any(e.kind == EntryKind.API_REST for e in fr.entries)


def test_csharp_aspnet_entry_treesitter(tmp_path: Path) -> None:
    pytest.importorskip("tree_sitter_c_sharp")
    c = tmp_path / "Api.cs"
    c.write_text(
        """
        [ApiController]
        class Api {
            [HttpGet("/items")]
            public void List() {}
        }
        """.strip(),
        encoding="utf-8",
    )
    reg = ParserRegistry()
    register_defaults(reg)
    fr = parse_source_file(reg, c, tmp_path, "csharp", "auto")
    assert fr is not None
    assert any(e.kind == EntryKind.API_REST for e in fr.entries)


def test_emit_cfg_ir_rust(tmp_path: Path) -> None:
    pytest.importorskip("tree_sitter_rust")
    p = tmp_path / "m.rs"
    p.write_text("fn f() { let x = 1; }\n", encoding="utf-8")
    reg = ParserRegistry()
    register_defaults(reg)
    fr = parse_source_file(reg, p, tmp_path, "rust", "auto")
    assert fr is not None
    cfg = ScanConfig(project_root=tmp_path, output_path=tmp_path / "out", emit_cfg=True)
    enrich_parse_results_with_ir([fr], cfg, tmp_path)
    assert fr.ir_methods


def test_lang_for_path_new_exts() -> None:
    assert lang_for_path(Path("x.rs")) == "rust"
    assert lang_for_path(Path("y.kt")) == "kotlin"
    assert lang_for_path(Path("z.cs")) == "csharp"
