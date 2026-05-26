from __future__ import annotations

from pathlib import Path

import pytest

from md_generator.codeflow.core.run_config import ScanConfig
from md_generator.codeflow.lang_dispatch import lang_for_path
from md_generator.codeflow.parsers.base import ParserRegistry, register_defaults
from md_generator.codeflow.parsers.ir_enrich import enrich_parse_results_with_ir
from md_generator.codeflow.parsers.unified_parser import parse_source_file

_EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.mark.parametrize(
    "lang,path,import_mod",
    [
        ("scala", _EXAMPLES / "mini_scala" / "Demo.scala", "tree_sitter_scala"),
        ("zig", _EXAMPLES / "mini_zig" / "demo.zig", "tree_sitter_zig"),
    ],
)
def test_treesitter_parse_and_cfg(lang: str, path: Path, import_mod: str, tmp_path: Path) -> None:
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
    cfg = ScanConfig(project_root=root, output_path=tmp_path / "out", emit_cfg=True)
    fr = parse_source_file(reg, path, root, lang, "auto")
    assert fr is not None
    enrich_parse_results_with_ir([fr], cfg, root)
    assert fr.ir_methods


def test_lang_for_path_scala_zig() -> None:
    assert lang_for_path(Path("App.scala")) == "scala"
    assert lang_for_path(Path("lib.sc")) == "scala"
    assert lang_for_path(Path("main.zig")) == "zig"
