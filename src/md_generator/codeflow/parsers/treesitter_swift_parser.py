"""Swift parsing via Tree-sitter (optional ``codeflow-treesitter`` extra)."""

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
from md_generator.codeflow.parsers.treesitter_entry_helpers import append_entry

logger = logging.getLogger(__name__)
_GRAMMAR_LABEL = "tree-sitter-swift"
_VAPOR_HTTP_ATTRS = frozenset({"Get", "Post", "Put", "Delete", "Patch", "Routes"})


def swift_language():
    return load_language("tree_sitter_swift", "language", package_label=_GRAMMAR_LABEL)


def _attr_name(node, source: bytes) -> str:  # noqa: ANN001
    for ch in node.children:
        if ch.type in ("identifier", "type_identifier", "simple_identifier"):
            return decode_text(source, ch).strip().lstrip("@")
    return decode_text(source, node).strip().lstrip("@").split("(")[0].split()[0]


def _attributes_on(node, source: bytes) -> set[str]:  # noqa: ANN001
    anns: set[str] = set()
    for ch in node.children:
        if ch.type == "attribute":
            anns.add(_attr_name(ch, source))
        elif ch.type == "modifiers":
            for sub in ch.children:
                if sub.type == "attribute":
                    anns.add(_attr_name(sub, source))
    return anns


class TreesitterSwiftParser:
    language = "swift"

    def parse_file(self, path: Path, project_root: Path) -> FileParseResult:
        root = project_root.resolve()
        key = rel_key(path, root)
        fr = FileParseResult(
            path=path.resolve(),
            language=self.language,
            parse_backend="treesitter",
            grammar_package=_GRAMMAR_LABEL,
        )
        loaded = swift_language()
        if loaded is None:
            return fr
        lang, _ = loaded
        source = path.read_bytes()
        tree = Parser(lang).parse(source)
        mark_parse_errors(fr, tree.root_node, path, language=self.language)

        state = _SwiftWalkState(fr, source, key, path)
        state.visit(tree.root_node)
        return fr


class _SwiftWalkState:
    def __init__(self, fr: FileParseResult, source: bytes, key: str, path: Path) -> None:
        self.fr = fr
        self.source = source
        self.key = key
        self.path = path
        self.type_stack: list[str] = []
        self.current_method: str | None = None
        self._entry_seen: set[str] = set()
        self._fp = str(path.resolve())

    @property
    def fq_type(self) -> str:
        return ".".join(self.type_stack) if self.type_stack else ""

    def visit(self, node) -> None:  # noqa: ANN001
        t = node.type
        if t == "import_declaration":
            name = node.child_by_field_name("name")
            if not name:
                for ch in node.children:
                    if ch.type == "identifier":
                        name = ch
                        break
            if name:
                append_import_edge(
                    self.fr,
                    self.key,
                    decode_text(self.source, name).strip(),
                    line=node.start_point[0] + 1,
                )
            return
        if t in ("class_declaration", "struct_declaration"):
            self._visit_type(node)
            return
        if t == "function_declaration":
            self._on_function(node, self.fq_type or None)
            return
        for ch in node.children:
            self.visit(ch)

    def _visit_type(self, node) -> None:  # noqa: ANN001
        name = node.child_by_field_name("name")
        if not name:
            return
        tname = decode_text(self.source, name).strip()
        self.type_stack.append(tname)
        for ch in node.children:
            if ch.type == "function_declaration":
                self._on_function(ch, self.fq_type)
            elif ch.type in ("class_declaration", "struct_declaration"):
                self._visit_type(ch)
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
        attrs = _attributes_on(node, self.source)
        if attrs & _VAPOR_HTTP_ATTRS:
            append_entry(
                self.fr,
                seen=self._entry_seen,
                symbol_id=caller,
                label="Vapor HTTP route",
                file_path=self._fp,
                line=node.start_point[0] + 1,
            )
        prev = self.current_method
        self.current_method = caller
        body = function_body_node(node)
        if body:
            walk_tree(body, self._visit_in_function)
        self.current_method = prev

    def _visit_in_function(self, node) -> None:  # noqa: ANN001
        if not self.current_method:
            return
        if node.type == "call_expression":
            callee = "call"
            for ch in node.children:
                if ch.type in ("simple_identifier", "identifier"):
                    callee = decode_text(self.source, ch).strip()
                    break
            record_call(
                self.fr,
                self.current_method,
                callee,
                line=node.start_point[0] + 1,
            )
