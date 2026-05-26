"""Scala parsing via Tree-sitter (optional ``codeflow-treesitter`` extra)."""

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
_GRAMMAR_LABEL = "tree-sitter-scala"


def scala_language():
    return load_language("tree_sitter_scala", "language", package_label=_GRAMMAR_LABEL)


class TreesitterScalaParser:
    language = "scala"

    def parse_file(self, path: Path, project_root: Path) -> FileParseResult:
        key = rel_key(path, project_root)
        fr = FileParseResult(
            path=path.resolve(),
            language=self.language,
            parse_backend="treesitter",
            grammar_package=_GRAMMAR_LABEL,
        )
        loaded = scala_language()
        if loaded is None:
            return fr
        lang, _ = loaded
        source = path.read_bytes()
        tree = Parser(lang).parse(source)
        mark_parse_errors(fr, tree.root_node, path, language=self.language)

        state = _ScalaWalkState(fr, source, key)
        state.visit(tree.root_node)
        return fr


class _ScalaWalkState:
    def __init__(self, fr: FileParseResult, source: bytes, key: str) -> None:
        self.fr = fr
        self.source = source
        self.key = key
        self.type_stack: list[str] = []
        self.current_method: str | None = None

    @property
    def fq_type(self) -> str:
        return ".".join(self.type_stack) if self.type_stack else ""

    def visit(self, node) -> None:  # noqa: ANN001
        t = node.type
        if t == "import_declaration":
            for ch in node.children:
                if ch.type in ("identifier", "stable_identifier", "select_identifier"):
                    raw = decode_text(self.source, ch).strip()
                    if raw:
                        append_import_edge(
                            self.fr,
                            self.key,
                            raw,
                            line=node.start_point[0] + 1,
                        )
                    break
            return
        if t in ("class_definition", "object_definition", "trait_definition"):
            self._visit_type(node)
            return
        if t in ("function_definition", "function_declaration"):
            self._on_function(node, self.fq_type or None)
            return
        for ch in node.children:
            self.visit(ch)

    def _visit_type(self, node) -> None:  # noqa: ANN001
        name = node.child_by_field_name("name")
        if not name:
            for ch in node.children:
                if ch.type == "identifier":
                    name = ch
                    break
        if not name:
            return
        tname = decode_text(self.source, name).strip()
        self.type_stack.append(tname)
        for ch in node.children:
            if ch.type in ("class_definition", "object_definition", "trait_definition"):
                self._visit_type(ch)
            elif ch.type in ("function_definition", "function_declaration"):
                self._on_function(ch, self.fq_type)
            else:
                self.visit(ch)
        self.type_stack.pop()

    def _on_function(self, node, fq: str | None) -> None:  # noqa: ANN001
        name = node.child_by_field_name("name")
        if not name:
            return
        mname = decode_text(self.source, name).strip()
        caller = sid(self.key, fq, mname)
        self.fr.symbol_ids.append(caller)
        prev = self.current_method
        self.current_method = caller
        body = function_body_node(node)
        if body:
            walk_tree(body, self._visit_in_function)
        self.current_method = prev

    def _visit_in_function(self, node) -> None:  # noqa: ANN001
        if not self.current_method:
            return
        if node.type in ("call_expression", "infix_expression", "generic_function"):
            callee = "call"
            fn = node.child_by_field_name("function") or node.child_by_field_name("name")
            if fn:
                callee = decode_text(self.source, fn).strip()
            else:
                for ch in node.children:
                    if ch.type in ("identifier", "field_identifier", "simple_identifier"):
                        callee = decode_text(self.source, ch).strip()
                        break
            record_call(
                self.fr,
                self.current_method,
                callee,
                line=node.start_point[0] + 1,
            )
