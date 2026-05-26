from __future__ import annotations

from pathlib import Path

import pytest

from md_generator.codeflow.lang_dispatch import lang_for_path
from md_generator.codeflow.parsers.base import ParserRegistry, register_defaults
from md_generator.codeflow.parsers.ir_enrich import enrich_parse_results_with_ir
from md_generator.codeflow.parsers.unified_parser import parse_source_file
from md_generator.codeflow.core.run_config import ScanConfig

_EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.mark.parametrize(
    "lang,path,import_mod",
    [
        ("swift", _EXAMPLES / "mini_swift" / "Demo.swift", "tree_sitter_swift"),
        ("ruby", _EXAMPLES / "mini_ruby" / "demo.rb", "tree_sitter_ruby"),
        ("lua", _EXAMPLES / "mini_lua" / "demo.lua", "tree_sitter_lua"),
    ],
)
def test_treesitter_auto_and_mode(lang: str, path: Path, import_mod: str, tmp_path: Path) -> None:
    pytest.importorskip(import_mod)
    if not path.is_file():
        pytest.skip(f"missing fixture {path}")
    reg = ParserRegistry()
    register_defaults(reg)
    root = path.parent
    for mode in ("auto", "treesitter"):
        fr = parse_source_file(reg, path, root, lang, mode)
        assert fr is not None
        assert fr.parse_backend == "treesitter"
        assert fr.symbol_ids
        assert fr.calls


def test_swift_symbol_id_format() -> None:
    pytest.importorskip("tree_sitter_swift")
    path = _EXAMPLES / "mini_swift" / "Demo.swift"
    if not path.is_file():
        pytest.skip("missing mini_swift fixture")
    reg = ParserRegistry()
    register_defaults(reg)
    fr = parse_source_file(reg, path, path.parent, "swift", "auto")
    assert fr is not None
    assert any("Demo.swift::" in s and s.endswith(".a") for s in fr.symbol_ids)


def test_emit_cfg_ir_lua(tmp_path: Path) -> None:
    pytest.importorskip("tree_sitter_lua")
    path = _EXAMPLES / "mini_lua" / "demo.lua"
    if not path.is_file():
        pytest.skip("missing mini_lua fixture")
    reg = ParserRegistry()
    register_defaults(reg)
    fr = parse_source_file(reg, path, path.parent, "lua", "auto")
    assert fr is not None
    cfg = ScanConfig(project_root=path.parent, output_path=tmp_path / "out", emit_cfg=True)
    enrich_parse_results_with_ir([fr], cfg, path.parent)
    assert fr.ir_methods


def test_lang_for_path_swift_ruby_lua() -> None:
    assert lang_for_path(Path("x.swift")) == "swift"
    assert lang_for_path(Path("y.rb")) == "ruby"
    assert lang_for_path(Path("z.lua")) == "lua"
