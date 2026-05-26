"""Ruby parsing via Tree-sitter (optional ``codeflow-treesitter`` extra)."""

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
    walk_tree,
)

logger = logging.getLogger(__name__)
_GRAMMAR_LABEL = "tree-sitter-ruby"


def ruby_language():
    return load_language("tree_sitter_ruby", "language", package_label=_GRAMMAR_LABEL)


class TreesitterRubyParser:
    language = "ruby"

    def parse_file(self, path: Path, project_root: Path) -> FileParseResult:
        root = project_root.resolve()
        key = rel_key(path, root)
        fr = FileParseResult(
            path=path.resolve(),
            language=self.language,
            parse_backend="treesitter",
            grammar_package=_GRAMMAR_LABEL,
        )
        loaded = ruby_language()
        if loaded is None:
            return fr
        lang, _ = loaded
        source = path.read_bytes()
        tree = Parser(lang).parse(source)
        mark_parse_errors(fr, tree.root_node, path, language=self.language)

        state = _RubyWalkState(fr, source, key, path)
        state.visit(tree.root_node)
        return fr


class _RubyWalkState:
    def __init__(self, fr: FileParseResult, source: bytes, key: str, path: Path) -> None:
        self.fr = fr
        self.source = source
        self.key = key
        self.path = path
        self.class_stack: list[str] = []
        self.current_method: str | None = None

    @property
    def fq_class(self) -> str:
        return "::".join(self.class_stack) if self.class_stack else ""

    def visit(self, node) -> None:  # noqa: ANN001
        t = node.type
        if t == "class":
            self._visit_class(node)
            return
        if t in ("method", "singleton_method"):
            self._on_method(node)
            return
        if t == "call":
            self._on_call(node)
            return
        for ch in node.children:
            self.visit(ch)

    def _visit_class(self, node) -> None:  # noqa: ANN001
        name = node.child_by_field_name("name")
        if not name:
            return
        cname = decode_text(self.source, name).strip()
        if not cname:
            return
        self.class_stack.append(cname)
        for ch in node.children:
            if ch.type == "class":
                self._visit_class(ch)
            elif ch.type in ("method", "singleton_method"):
                self._on_method(ch)
            else:
                self.visit(ch)
        self.class_stack.pop()

    def _on_method(self, node) -> None:  # noqa: ANN001
        name = node.child_by_field_name("name")
        if not name:
            return
        mname = decode_text(self.source, name).strip()
        fq = self.fq_class or None
        caller = sid(self.key, fq, mname)
        self.fr.symbol_ids.append(caller)
        prev = self.current_method
        self.current_method = caller
        for ch in node.children:
            self.visit(ch)
        self.current_method = prev

    def _on_call(self, node) -> None:  # noqa: ANN001
        callee = "call"
        ident = node.child_by_field_name("name") or node.child_by_field_name("method")
        if ident:
            callee = decode_text(self.source, ident).strip()
        else:
            for ch in node.children:
                if ch.type == "identifier":
                    callee = decode_text(self.source, ch).strip()
                    break
        if callee in ("require", "require_relative"):
            for ch in node.children:
                if ch.type == "argument_list":
                    for arg in ch.children:
                        if arg.type == "string":
                            raw = decode_text(self.source, arg).strip().strip("\"'")
                            if raw:
                                append_import_edge(
                                    self.fr,
                                    self.key,
                                    raw,
                                    line=node.start_point[0] + 1,
                                )
                            return
        if not self.current_method:
            return
        record_call(
            self.fr,
            self.current_method,
            callee,
            line=node.start_point[0] + 1,
        )
