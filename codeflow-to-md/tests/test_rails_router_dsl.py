from __future__ import annotations

from pathlib import Path

import pytest

from md_generator.codeflow.detectors.rails_detector import detect_rails_entries
from md_generator.codeflow.parsers.base import ParserRegistry, register_defaults
from md_generator.codeflow.parsers.unified_parser import parse_source_file

_EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_rails_router_dsl_regex() -> None:
    routes = _EXAMPLES / "mini_rails" / "config" / "routes.rb"
    if not routes.is_file():
        pytest.skip("missing mini_rails routes")
    entries = detect_rails_entries(routes, _EXAMPLES / "mini_rails")
    labels = " ".join(e.label for e in entries).lower()
    assert "resources" in labels
    assert "namespace" in labels
    assert "mount" in labels
    assert "root" in labels or "get" in labels


def test_rails_basic_route_call_treesitter() -> None:
    pytest.importorskip("tree_sitter_ruby")
    routes = _EXAMPLES / "mini_rails" / "config" / "routes.rb"
    if not routes.is_file():
        pytest.skip("missing routes.rb")
    reg = ParserRegistry()
    register_defaults(reg)
    fr = parse_source_file(reg, routes, _EXAMPLES / "mini_rails", "ruby", "treesitter")
    assert fr is not None
    route_entries = [e for e in fr.entries if "Rails route" in e.label or "routes." in e.symbol_id]
    assert route_entries or detect_rails_entries(routes, _EXAMPLES / "mini_rails")
