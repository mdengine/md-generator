"""Lua parsing via Tree-sitter (optional ``codeflow-treesitter`` extra)."""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Parser

from md_generator.codeflow.models.ir import FileParseResult
from md_generator.codeflow.parsers.treesitter_common import (
    append_import_edge,
    decode_text,
    function_body_node,
    load_language,
    mark_parse_errors,
    record_call,
    rel_key,
    sid,
    walk_tree,
)

logger = logging.getLogger(__name__)
_GRAMMAR_LABEL = "tree-sitter-lua"


def lua_language():
    return load_language("tree_sitter_lua", "language", package_label=_GRAMMAR_LABEL)


class TreesitterLuaParser:
    language = "lua"

    def parse_file(self, path: Path, project_root: Path) -> FileParseResult:
        key = rel_key(path, project_root)
        fr = FileParseResult(
            path=path.resolve(),
            language=self.language,
            parse_backend="treesitter",
            grammar_package=_GRAMMAR_LABEL,
        )
        loaded = lua_language()
        if loaded is None:
            return fr
        lang, _ = loaded
        source = path.read_bytes()
        tree = Parser(lang).parse(source)
        mark_parse_errors(fr, tree.root_node, path, language=self.language)

        state = _LuaWalkState(fr, source, key, path)
        state.visit(tree.root_node)
        return fr


class _LuaWalkState:
    def __init__(self, fr: FileParseResult, source: bytes, key: str, path: Path) -> None:
        self.fr = fr
        self.source = source
        self.key = key
        self.path = path
        self.current_method: str | None = None

    def visit(self, node) -> None:  # noqa: ANN001
        if node.type == "function_declaration":
            self._on_function(node)
            return
        if node.type == "function_call":
            self._on_call(node)
            return
        for ch in node.children:
            self.visit(ch)

    def _on_function(self, node) -> None:  # noqa: ANN001
        name = node.child_by_field_name("name")
        if not name:
            return
        mname = decode_text(self.source, name).strip()
        caller = sid(self.key, None, mname)
        self.fr.symbol_ids.append(caller)
        prev = self.current_method
        self.current_method = caller
        body = function_body_node(node)
        if body:
            walk_tree(body, self._visit_in_function)
        self.current_method = prev

    def _on_call(self, node) -> None:  # noqa: ANN001
        fn = node.child_by_field_name("name")
        callee = decode_text(self.source, fn).strip() if fn else "call"
        if callee in ("require", "dofile", "loadfile"):
            for ch in node.children:
                if ch.type == "string":
                    raw = decode_text(self.source, ch).strip().strip("\"'")
                    if raw:
                        append_import_edge(
                            self.fr,
                            self.key,
                            raw,
                            line=node.start_point[0] + 1,
                        )
                    return
        if self.current_method:
            record_call(
                self.fr,
                self.current_method,
                callee,
                line=node.start_point[0] + 1,
            )

    def _visit_in_function(self, node) -> None:  # noqa: ANN001
        if node.type == "function_call":
            self._on_call(node)
