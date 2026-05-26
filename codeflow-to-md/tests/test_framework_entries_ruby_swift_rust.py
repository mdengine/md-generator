from __future__ import annotations

from pathlib import Path

import pytest

from md_generator.codeflow.detectors.entry_detector import apply_entry_detectors
from md_generator.codeflow.models.ir import EntryKind, FileParseResult
from md_generator.codeflow.parsers.base import ParserRegistry, register_defaults
from md_generator.codeflow.parsers.unified_parser import parse_source_file

_EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def _parse(lang: str, path: Path, root: Path):
    reg = ParserRegistry()
    register_defaults(reg)
    return parse_source_file(reg, path, root, lang, "treesitter")


def test_rails_controller_entries() -> None:
    pytest.importorskip("tree_sitter_ruby")
    ctrl = _EXAMPLES / "mini_rails" / "app" / "controllers" / "items_controller.rb"
    if not ctrl.is_file():
        pytest.skip("missing mini_rails fixture")
    fr = _parse("ruby", ctrl, _EXAMPLES / "mini_rails")
    assert fr is not None
    assert any(e.label == "Rails controller action" for e in fr.entries)
    assert any("index" in e.symbol_id for e in fr.entries)


def test_sinatra_route_entries() -> None:
    pytest.importorskip("tree_sitter_ruby")
    app_rb = _EXAMPLES / "mini_sinatra" / "app.rb"
    if not app_rb.is_file():
        pytest.skip("missing mini_sinatra fixture")
    fr = _parse("ruby", app_rb, _EXAMPLES / "mini_sinatra")
    assert fr is not None
    assert any("sinatra" in e.symbol_id.lower() or "Sinatra" in e.label for e in fr.entries)


def test_vapor_route_entries() -> None:
    pytest.importorskip("tree_sitter_swift")
    routes = _EXAMPLES / "mini_vapor" / "Routes.swift"
    if not routes.is_file():
        pytest.skip("missing mini_vapor fixture")
    fr = _parse("swift", routes, _EXAMPLES / "mini_vapor")
    assert fr is not None
    assert any(e.kind == EntryKind.API_REST and "Vapor" in e.label for e in fr.entries)


def test_actix_route_entries() -> None:
    pytest.importorskip("tree_sitter_rust")
    main_rs = _EXAMPLES / "mini_actix" / "src" / "main.rs"
    if not main_rs.is_file():
        pytest.skip("missing mini_actix fixture")
    fr = _parse("rust", main_rs, _EXAMPLES / "mini_actix")
    assert fr is not None
    assert any("Actix" in e.label for e in fr.entries)


def test_axum_route_entries() -> None:
    pytest.importorskip("tree_sitter_rust")
    main_rs = _EXAMPLES / "mini_axum" / "src" / "main.rs"
    if not main_rs.is_file():
        pytest.skip("missing mini_axum fixture")
    fr = _parse("rust", main_rs, _EXAMPLES / "mini_axum")
    assert fr is not None
    assert any("Axum" in e.label for e in fr.entries)


def test_action_cable_channel_entries() -> None:
    pytest.importorskip("tree_sitter_ruby")
    ch = _EXAMPLES / "mini_action_cable" / "app" / "channels" / "chat_channel.rb"
    if not ch.is_file():
        pytest.skip("missing mini_action_cable fixture")
    fr = _parse("ruby", ch, _EXAMPLES / "mini_action_cable")
    assert fr is not None
    assert any(e.kind == EntryKind.QUEUE for e in fr.entries)


def test_rails_detector_on_routes_file() -> None:
    routes = _EXAMPLES / "mini_rails" / "config" / "routes.rb"
    if not routes.is_file():
        pytest.skip("missing routes.rb")
    pr = FileParseResult(path=routes.resolve(), language="ruby")
    apply_entry_detectors([routes], _EXAMPLES / "mini_rails", [pr])
    labels = {e.label for e in pr.entries}
    assert any("resources" in lb.lower() for lb in labels)
    assert any("namespace" in lb.lower() for lb in labels)
    assert any("mount" in lb.lower() for lb in labels)
