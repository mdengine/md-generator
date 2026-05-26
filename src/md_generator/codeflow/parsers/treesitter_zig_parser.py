"""Zig parsing via Tree-sitter (optional ``codeflow-treesitter`` extra)."""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Parser

from md_generator.codeflow.models.ir import FileParseResult
from md_generator.codeflow.parsers.treesitter_common import (
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
_GRAMMAR_LABEL = "tree-sitter-zig"


def zig_language():
    return load_language("tree_sitter_zig", "language", package_label=_GRAMMAR_LABEL)


class TreesitterZigParser:
    language = "zig"

    def parse_file(self, path: Path, project_root: Path) -> FileParseResult:
        key = rel_key(path, project_root)
        fr = FileParseResult(
            path=path.resolve(),
            language=self.language,
            parse_backend="treesitter",
            grammar_package=_GRAMMAR_LABEL,
        )
        loaded = zig_language()
        if loaded is None:
            return fr
        lang, _ = loaded
        source = path.read_bytes()
        tree = Parser(lang).parse(source)
        mark_parse_errors(fr, tree.root_node, path, language=self.language)

        current: str | None = None
        stack = [tree.root_node]
        while stack:
            n = stack.pop()
            if n.type == "function_declaration":
                name = n.child_by_field_name("name")
                if name:
                    mname = decode_text(source, name).strip()
                    current = sid(key, None, mname)
                    fr.symbol_ids.append(current)
                    body = function_body_node(n)
                    if body and current:

                        def visit_fn(node) -> None:  # noqa: ANN001
                            if node.type == "call_expression" and current:
                                fn = node.child_by_field_name("function")
                                callee = decode_text(source, fn).strip() if fn else "call"
                                record_call(
                                    fr,
                                    current,
                                    callee,
                                    line=node.start_point[0] + 1,
                                )

                        walk_tree(body, visit_fn)
            stack.extend(reversed(n.children))
        return fr
