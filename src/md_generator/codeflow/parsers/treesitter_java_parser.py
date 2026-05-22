"""Java parsing via Tree-sitter (optional ``codeflow-treesitter`` extra)."""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Parser

from md_generator.codeflow.graph.relations import REL_IMPLEMENTS, REL_INHERITS
from md_generator.codeflow.models.ir import (
    BranchPoint,
    EntryKind,
    EntryRecord,
    FileParseResult,
    StructuralEdge,
)
from md_generator.codeflow.parsers.treesitter_common import (
    append_import_edge,
    annotation_simple_name,
    decode_text,
    load_language,
    record_call,
    rel_key,
    sid,
    trim,
    walk_tree,
)

logger = logging.getLogger(__name__)

_GRAMMAR_LABEL = "tree-sitter-java"
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


def java_language():
    return load_language("tree_sitter_java", "language", package_label=_GRAMMAR_LABEL)


class TreesitterJavaParser:
    language = "java"

    def parse_file(self, path: Path, project_root: Path) -> FileParseResult:
        root = project_root.resolve()
        key = rel_key(path, root)
        fr = FileParseResult(
            path=path.resolve(),
            language=self.language,
            parse_backend="treesitter",
            grammar_package=_GRAMMAR_LABEL,
        )
        loaded = java_language()
        if loaded is None:
            return fr
        lang, _ = loaded
        source = path.read_bytes()
        parser = Parser(lang)
        tree = parser.parse(source)
        if tree.root_node.has_error:
            logger.debug("tree-sitter java parse has errors: %s", path)

        state = _JavaWalkState(fr, source, key, path)
        for ch in tree.root_node.children:
            state.visit_top(ch)
        return fr


def _modifiers_node(node) -> object | None:  # noqa: ANN001
    mods = node.child_by_field_name("modifiers")
    if mods:
        return mods
    for ch in node.children:
        if ch.type == "modifiers":
            return ch
    return None


def _annotations_on(node, source: bytes) -> set[str]:  # noqa: ANN001
    anns: set[str] = set()
    mods = _modifiers_node(node)
    if mods:
        for ch in mods.children:
            if ch.type in ("marker_annotation", "annotation"):
                anns.add(annotation_simple_name(ch, source))
    for ch in node.children:
        if ch.type in ("marker_annotation", "annotation"):
            anns.add(annotation_simple_name(ch, source))
    return anns


class _JavaWalkState:
    def __init__(self, fr: FileParseResult, source: bytes, key: str, path: Path) -> None:
        self.fr = fr
        self.source = source
        self.key = key
        self.path = path
        self.class_stack: list[str] = []
        self.class_anns: list[set[str]] = []
        self.current_method: str | None = None
        self.cond_stack: list[str] = []

    @property
    def fq_class(self) -> str:
        return ".".join(self.class_stack) if self.class_stack else ""

    def visit_top(self, node) -> None:  # noqa: ANN001
        t = node.type
        if t == "package_declaration":
            scoped = node.child_by_field_name("name")
            if scoped:
                self.fr.java_package = decode_text(self.source, scoped).strip()
        elif t == "import_declaration":
            scoped = node.child_by_field_name("name")
            if scoped:
                append_import_edge(
                    self.fr,
                    self.key,
                    decode_text(self.source, scoped).strip(),
                    line=node.start_point[0] + 1,
                )
        elif t in ("class_declaration", "interface_declaration", "enum_declaration"):
            self._parse_type(node)

    def _parse_type(self, node) -> None:  # noqa: ANN001
        name_n = node.child_by_field_name("name")
        if not name_n:
            return
        name = decode_text(self.source, name_n).strip()
        anns = _annotations_on(node, self.source)
        self.class_stack.append(name)
        self.class_anns.append(anns)
        for ch in node.children:
            if ch.type == "superclass":
                self._inheritance(ch, REL_INHERITS)
            elif ch.type == "super_interfaces":
                for sub in ch.children:
                    if sub.type in ("type_identifier", "scoped_type_identifier"):
                        self._type_edge(sub, REL_IMPLEMENTS)
        body = node.child_by_field_name("body")
        if body:
            for ch in body.children:
                if ch.type == "method_declaration":
                    self._on_method(ch)
                elif ch.type in ("class_declaration", "interface_declaration", "enum_declaration"):
                    self._parse_type(ch)
        self.class_stack.pop()
        self.class_anns.pop()

    def _on_method(self, node) -> None:  # noqa: ANN001
        name_n = node.child_by_field_name("name")
        if not name_n:
            return
        mname = decode_text(self.source, name_n).strip()
        caller = sid(self.key, self.fq_class, mname)
        self.fr.symbol_ids.append(caller)
        prev = self.current_method
        self.current_method = caller
        manns = _annotations_on(node, self.source)
        class_anns = self.class_anns[-1] if self.class_anns else set()
        if (class_anns & _SPRING_CLASS_ANNS) and (manns & _SPRING_METHOD_ANNS):
            self.fr.entries.append(
                EntryRecord(
                    symbol_id=caller,
                    kind=EntryKind.API_REST,
                    label="Java Spring MVC mapping",
                    file_path=str(self.path.resolve()),
                    line=node.start_point[0] + 1,
                ),
            )
        body = node.child_by_field_name("body")
        if body:
            walk_tree(body, self._visit_in_method)
        self.current_method = prev

    def _visit_in_method(self, node) -> None:  # noqa: ANN001
        if node.type == "method_invocation" and self.current_method:
            self._on_call(node)

    def _on_call(self, node) -> None:  # noqa: ANN001
        if not self.current_method:
            return
        obj = node.child_by_field_name("object")
        name = node.child_by_field_name("name")
        parts: list[str] = []
        if obj:
            parts.append(decode_text(self.source, obj).strip())
        if name:
            parts.append(decode_text(self.source, name).strip())
        callee = ".".join(p for p in parts if p) or "call"
        cond = self.cond_stack[-1] if self.cond_stack else None
        record_call(
            self.fr,
            self.current_method,
            callee,
            line=node.start_point[0] + 1,
            condition_label=cond,
        )

    def _inheritance(self, node, relation: str) -> None:  # noqa: ANN001
        if not self.class_stack:
            return
        cid = f"class:{self.key}::{self.fq_class}"
        for ch in node.children:
            if ch.type in ("type_identifier", "scoped_type_identifier"):
                tgt = decode_text(self.source, ch).strip()
                if tgt:
                    self.fr.structural_edges.append(
                        StructuralEdge(
                            source_id=cid,
                            target_id=f"external::{tgt}",
                            relation=relation,
                            confidence=0.7,
                            line=node.start_point[0] + 1,
                        ),
                    )

    def _type_edge(self, node, relation: str) -> None:  # noqa: ANN001
        if not self.class_stack:
            return
        tgt = decode_text(self.source, node).strip()
        if not tgt:
            return
        cid = f"class:{self.key}::{self.fq_class}"
        self.fr.structural_edges.append(
            StructuralEdge(
                source_id=cid,
                target_id=f"external::{tgt}",
                relation=relation,
                confidence=0.7,
                line=node.start_point[0] + 1,
            ),
        )
