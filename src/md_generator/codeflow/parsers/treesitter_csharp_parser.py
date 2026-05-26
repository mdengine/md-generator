"""C# parsing via Tree-sitter (optional ``codeflow-treesitter`` extra)."""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Parser

from md_generator.codeflow.models.ir import EntryKind, EntryRecord, FileParseResult
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
_GRAMMAR_LABEL = "tree-sitter-c-sharp"
_ASPNET_CLASS_ATTRS = frozenset({"ApiController", "Controller"})
_ASPNET_METHOD_ATTRS = frozenset({"HttpGet", "HttpPost", "HttpPut", "HttpDelete", "HttpPatch", "Route"})


def csharp_language():
    return load_language("tree_sitter_c_sharp", "language", package_label=_GRAMMAR_LABEL)


def _attr_name(node, source: bytes) -> str:  # noqa: ANN001
    name = node.child_by_field_name("name") or node.child_by_field_name("identifier")
    if name:
        return decode_text(source, name).strip().lstrip("[").rstrip("]")
    return decode_text(source, node).strip().lstrip("[").split("(")[0].split("]")[0]


def _attributes_on(node, source: bytes) -> set[str]:  # noqa: ANN001
    anns: set[str] = set()
    for ch in node.children:
        if ch.type == "attribute_list":
            for sub in ch.children:
                if sub.type == "attribute":
                    anns.add(_attr_name(sub, source))
        elif ch.type == "attribute":
            anns.add(_attr_name(ch, source))
    return anns


class TreesitterCsharpParser:
    language = "csharp"

    def parse_file(self, path: Path, project_root: Path) -> FileParseResult:
        root = project_root.resolve()
        key = rel_key(path, root)
        fr = FileParseResult(
            path=path.resolve(),
            language=self.language,
            parse_backend="treesitter",
            grammar_package=_GRAMMAR_LABEL,
        )
        loaded = csharp_language()
        if loaded is None:
            return fr
        lang, _ = loaded
        source = path.read_bytes()
        tree = Parser(lang).parse(source)
        mark_parse_errors(fr, tree.root_node, path, language=self.language)

        state = _CsharpWalkState(fr, source, key, path)
        state.visit(tree.root_node)
        return fr


class _CsharpWalkState:
    def __init__(self, fr: FileParseResult, source: bytes, key: str, path: Path) -> None:
        self.fr = fr
        self.source = source
        self.key = key
        self.path = path
        self.class_stack: list[str] = []
        self.class_attrs: list[set[str]] = []
        self.current_method: str | None = None

    @property
    def fq_class(self) -> str:
        return ".".join(self.class_stack) if self.class_stack else ""

    def visit(self, node) -> None:  # noqa: ANN001
        t = node.type
        if t == "using_directive":
            name = node.child_by_field_name("name")
            if name:
                append_import_edge(
                    self.fr,
                    self.key,
                    decode_text(self.source, name).strip(),
                    line=node.start_point[0] + 1,
                )
            return
        if t == "class_declaration":
            self._visit_class(node)
            return
        for ch in node.children:
            self.visit(ch)

    def _visit_class(self, node) -> None:  # noqa: ANN001
        name = node.child_by_field_name("name")
        if not name:
            return
        cname = decode_text(self.source, name).strip()
        self.class_stack.append(cname)
        self.class_attrs.append(_attributes_on(node, self.source))
        for ch in node.children:
            if ch.type == "method_declaration":
                self._on_method(ch)
            elif ch.type == "class_declaration":
                self._visit_class(ch)
            elif ch.type == "declaration_list":
                self._visit_declaration_list(ch)
            else:
                self.visit(ch)
        self.class_stack.pop()
        self.class_attrs.pop()

    def _visit_declaration_list(self, node) -> None:  # noqa: ANN001
        for ch in node.children:
            if ch.type == "method_declaration":
                self._on_method(ch)
            elif ch.type == "class_declaration":
                self._visit_class(ch)
            else:
                self.visit(ch)

    def _on_method(self, node) -> None:  # noqa: ANN001
        name = node.child_by_field_name("name")
        if not name:
            return
        mname = decode_text(self.source, name).strip()
        caller = sid(self.key, self.fq_class or None, mname)
        self.fr.symbol_ids.append(caller)
        prev = self.current_method
        self.current_method = caller
        mattrs = _attributes_on(node, self.source)
        cattrs = self.class_attrs[-1] if self.class_attrs else set()
        if (cattrs & _ASPNET_CLASS_ATTRS) and (mattrs & _ASPNET_METHOD_ATTRS):
            self.fr.entries.append(
                EntryRecord(
                    symbol_id=caller,
                    kind=EntryKind.API_REST,
                    label="ASP.NET API mapping",
                    file_path=str(self.path.resolve()),
                    line=node.start_point[0] + 1,
                ),
            )
        body = node.child_by_field_name("body")
        if body:
            walk_tree(body, self._visit_in_method)
        self.current_method = prev

    def _visit_in_method(self, node) -> None:  # noqa: ANN001
        if not self.current_method:
            return
        if node.type == "invocation_expression":
            fn = node.child_by_field_name("function")
            callee = decode_text(self.source, fn).strip() if fn else "call"
            record_call(
                self.fr,
                self.current_method,
                callee,
                line=node.start_point[0] + 1,
            )
