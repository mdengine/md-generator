"""Rust parsing via Tree-sitter (optional ``codeflow-treesitter`` extra)."""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Parser

from md_generator.codeflow.models.ir import FileParseResult
from md_generator.codeflow.parsers.treesitter_common import (
    append_import_edge,
    decode_text,
    load_language,
    mark_parse_errors,
    record_call,
    rel_key,
    sid,
)

logger = logging.getLogger(__name__)
_GRAMMAR_LABEL = "tree-sitter-rust"


def rust_language():
    return load_language("tree_sitter_rust", "language", package_label=_GRAMMAR_LABEL)


class TreesitterRustParser:
    language = "rust"

    def parse_file(self, path: Path, project_root: Path) -> FileParseResult:
        key = rel_key(path, project_root)
        fr = FileParseResult(
            path=path.resolve(),
            language=self.language,
            parse_backend="treesitter",
            grammar_package=_GRAMMAR_LABEL,
        )
        loaded = rust_language()
        if loaded is None:
            return fr
        lang, _ = loaded
        source = path.read_bytes()
        tree = Parser(lang).parse(source)
        mark_parse_errors(fr, tree.root_node, path, language=self.language)

        impl_type: str | None = None
        current: str | None = None
        stack = [tree.root_node]
        while stack:
            n = stack.pop()
            t = n.type
            if t == "impl_item":
                ty = n.child_by_field_name("type")
                impl_type = decode_text(source, ty).strip() if ty else None
            elif t == "function_item":
                name = n.child_by_field_name("name")
                if name:
                    mname = decode_text(source, name).strip()
                    current = sid(key, impl_type, mname) if impl_type else sid(key, None, mname)
                    fr.symbol_ids.append(current)
            elif t == "use_declaration":
                arg = n.child_by_field_name("argument")
                if arg:
                    append_import_edge(
                        fr,
                        key,
                        decode_text(source, arg).strip(),
                        line=n.start_point[0] + 1,
                    )
            elif t == "call_expression" and current:
                fn = n.child_by_field_name("function")
                callee = decode_text(source, fn).strip() if fn else "call"
                record_call(fr, current, callee, line=n.start_point[0] + 1)
            stack.extend(reversed(n.children))
        return fr
