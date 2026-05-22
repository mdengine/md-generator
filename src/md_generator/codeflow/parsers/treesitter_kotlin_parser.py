"""Kotlin parsing via Tree-sitter (optional ``codeflow-treesitter`` extra)."""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Parser

from md_generator.codeflow.models.ir import EntryKind, EntryRecord, FileParseResult
from md_generator.codeflow.parsers.treesitter_common import (
    annotation_simple_name,
    append_import_edge,
    decode_text,
    load_language,
    mark_parse_errors,
    record_call,
    rel_key,
    sid,
    function_body_node,
    walk_tree,
)

logger = logging.getLogger(__name__)
_GRAMMAR_LABEL = "tree-sitter-kotlin"
_SPRING_CLASS_ANNS = frozenset({"RestController", "Controller", "RequestMapping"})
_SPRING_METHOD_ANNS = frozenset(
    {
        "GetMapping",
        "PostMapping",
        "PutMapping",
        "DeleteMapping",
        "PatchMapping",
        "RequestMapping",
    },
)


def kotlin_language():
    return load_language("tree_sitter_kotlin", "language", package_label=_GRAMMAR_LABEL)


def _annotations_on(node, source: bytes) -> set[str]:  # noqa: ANN001
    anns: set[str] = set()
    for ch in node.children:
        if ch.type in ("annotation", "modifiers"):
            for sub in ch.children:
                if sub.type in ("annotation", "marker_annotation"):
                    anns.add(annotation_simple_name(sub, source))
        elif ch.type in ("annotation", "marker_annotation"):
            anns.add(annotation_simple_name(ch, source))
    return anns


class TreesitterKotlinParser:
    language = "kotlin"

    def parse_file(self, path: Path, project_root: Path) -> FileParseResult:
        root = project_root.resolve()
        key = rel_key(path, root)
        fr = FileParseResult(
            path=path.resolve(),
            language=self.language,
            parse_backend="treesitter",
            grammar_package=_GRAMMAR_LABEL,
        )
        loaded = kotlin_language()
        if loaded is None:
            return fr
        lang, _ = loaded
        source = path.read_bytes()
        tree = Parser(lang).parse(source)
        mark_parse_errors(fr, tree.root_node, path, language=self.language)

        state = _KotlinWalkState(fr, source, key, path)
        state.visit(tree.root_node)
        return fr


class _KotlinWalkState:
    def __init__(self, fr: FileParseResult, source: bytes, key: str, path: Path) -> None:
        self.fr = fr
        self.source = source
        self.key = key
        self.path = path
        self.class_stack: list[str] = []
        self.class_anns: list[set[str]] = []
        self.current_method: str | None = None

    @property
    def fq_class(self) -> str:
        return ".".join(self.class_stack) if self.class_stack else ""

    def visit(self, node) -> None:  # noqa: ANN001
        t = node.type
        if t == "import_header":
            ref = node.child_by_field_name("identifier") or node.child_by_field_name("reference")
            if ref:
                append_import_edge(
                    self.fr,
                    self.key,
                    decode_text(self.source, ref).strip(),
                    line=node.start_point[0] + 1,
                )
            return
        if t == "package_header":
            ref = node.child_by_field_name("identifier")
            if ref:
                append_import_edge(
                    self.fr,
                    self.key,
                    decode_text(self.source, ref).strip(),
                    line=node.start_point[0] + 1,
                )
            return
        if t == "class_declaration":
            self._visit_class(node)
            return
        if t == "function_declaration":
            self._on_function(node)
            return
        for ch in node.children:
            self.visit(ch)

    def _visit_class(self, node) -> None:  # noqa: ANN001
        name = node.child_by_field_name("name")
        if not name:
            return
        cname = decode_text(self.source, name).strip()
        self.class_stack.append(cname)
        self.class_anns.append(_annotations_on(node, self.source))
        for ch in node.children:
            if ch.type == "function_declaration":
                self._on_function(ch)
            elif ch.type == "class_declaration":
                self._visit_class(ch)
            else:
                self.visit(ch)
        self.class_stack.pop()
        self.class_anns.pop()

    def _on_function(self, node) -> None:  # noqa: ANN001
        name = node.child_by_field_name("name")
        if not name:
            return
        mname = decode_text(self.source, name).strip()
        caller = sid(self.key, self.fq_class or None, mname)
        self.fr.symbol_ids.append(caller)
        prev = self.current_method
        self.current_method = caller
        manns = _annotations_on(node, self.source)
        cans = self.class_anns[-1] if self.class_anns else set()
        if (cans & _SPRING_CLASS_ANNS) and (manns & _SPRING_METHOD_ANNS):
            self.fr.entries.append(
                EntryRecord(
                    symbol_id=caller,
                    kind=EntryKind.API_REST,
                    label="Kotlin Spring MVC mapping",
                    file_path=str(self.path.resolve()),
                    line=node.start_point[0] + 1,
                ),
            )
        body = function_body_node(node)
        if body:
            walk_tree(body, self._visit_in_function)
        self.current_method = prev

    def _visit_in_function(self, node) -> None:  # noqa: ANN001
        if not self.current_method:
            return
        if node.type in ("call_expression", "navigation_expression"):
            fn = node.child_by_field_name("function") or node.child_by_field_name("name")
            callee = decode_text(self.source, fn).strip() if fn else "call"
            record_call(
                self.fr,
                self.current_method,
                callee,
                line=node.start_point[0] + 1,
            )
