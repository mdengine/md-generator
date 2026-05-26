"""Python parsing via Tree-sitter (optional ``codeflow-treesitter`` extra)."""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Parser

from md_generator.codeflow.models.ir import FileParseResult
from md_generator.codeflow.parsers.treesitter_common import (
    append_import_edge,
    decode_text,
    load_language,
    record_call,
    rel_key,
    sid,
)

logger = logging.getLogger(__name__)
_GRAMMAR_LABEL = "tree-sitter-python"


def python_language():
    return load_language("tree_sitter_python", "language", package_label=_GRAMMAR_LABEL)


class TreesitterPythonParser:
    language = "python"

    def parse_file(self, path: Path, project_root: Path) -> FileParseResult:
        key = rel_key(path, project_root)
        fr = FileParseResult(
            path=path.resolve(),
            language=self.language,
            parse_backend="treesitter",
            grammar_package=_GRAMMAR_LABEL,
        )
        loaded = python_language()
        if loaded is None:
            return fr
        lang, _ = loaded
        source = path.read_bytes()
        tree = Parser(lang).parse(source)
        state = _PyState(fr, source, key)
        stack = [tree.root_node]
        while stack:
            n = stack.pop()
            state.visit(n)
            stack.extend(reversed(n.children))
        return fr


class _PyState:
    def __init__(self, fr: FileParseResult, source: bytes, key: str) -> None:
        self.fr = fr
        self.source = source
        self.key = key
        self.class_name: str | None = None
        self.current_fn: str | None = None

    def visit(self, node) -> None:  # noqa: ANN001
        t = node.type
        if t == "class_definition":
            name = node.child_by_field_name("name")
            self.class_name = decode_text(self.source, name).strip() if name else None
        elif t == "function_definition":
            name = node.child_by_field_name("name")
            if name:
                mname = decode_text(self.source, name).strip()
                self.current_fn = sid(self.key, self.class_name, mname)
                self.fr.symbol_ids.append(self.current_fn)
        elif t == "call" and self.current_fn:
            fn = node.child_by_field_name("function")
            callee = decode_text(self.source, fn).strip() if fn else "call"
            record_call(self.fr, self.current_fn, callee, line=node.start_point[0] + 1)
        elif t == "import_statement":
            name = node.child_by_field_name("name")
            if name:
                append_import_edge(
                    self.fr,
                    self.key,
                    decode_text(self.source, name).strip(),
                    line=node.start_point[0] + 1,
                )
        elif t == "import_from_statement":
            module = node.child_by_field_name("module_name")
            if module:
                append_import_edge(
                    self.fr,
                    self.key,
                    decode_text(self.source, module).strip(),
                    line=node.start_point[0] + 1,
                )
