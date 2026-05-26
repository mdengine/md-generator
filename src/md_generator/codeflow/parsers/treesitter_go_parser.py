"""Go parsing via Tree-sitter (optional ``codeflow-treesitter`` extra)."""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Parser

from md_generator.codeflow.models.ir import FileParseResult
from md_generator.codeflow.parsers.treesitter_common import (
    decode_text,
    load_language,
    record_call,
    rel_key,
    sid,
)

logger = logging.getLogger(__name__)
_GRAMMAR_LABEL = "tree-sitter-go"


def go_language():
    return load_language("tree_sitter_go", "language", package_label=_GRAMMAR_LABEL)


class TreesitterGoParser:
    language = "go"

    def parse_file(self, path: Path, project_root: Path) -> FileParseResult:
        key = rel_key(path, project_root)
        fr = FileParseResult(
            path=path.resolve(),
            language=self.language,
            parse_backend="treesitter",
            grammar_package=_GRAMMAR_LABEL,
        )
        loaded = go_language()
        if loaded is None:
            return fr
        lang, _ = loaded
        source = path.read_bytes()
        tree = Parser(lang).parse(source)
        recv: str | None = None
        current: str | None = None
        stack = [tree.root_node]
        while stack:
            n = stack.pop()
            t = n.type
            if t == "method_declaration":
                name = n.child_by_field_name("name")
                recv_n = n.child_by_field_name("receiver")
                if recv_n:
                    recv = decode_text(source, recv_n).strip().strip("()")
                if name:
                    mname = decode_text(source, name).strip()
                    current = sid(key, recv, mname) if recv else sid(key, None, mname)
                    fr.symbol_ids.append(current)
            elif t == "function_declaration":
                name = n.child_by_field_name("name")
                recv = None
                if name:
                    mname = decode_text(source, name).strip()
                    current = sid(key, None, mname)
                    fr.symbol_ids.append(current)
            elif t == "call_expression" and current:
                fn = n.child_by_field_name("function")
                callee = decode_text(source, fn).strip() if fn else "call"
                record_call(fr, current, callee, line=n.start_point[0] + 1)
            stack.extend(reversed(n.children))
        return fr
