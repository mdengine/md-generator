"""Ruby parsing via Tree-sitter (optional ``codeflow-treesitter`` extra)."""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Parser

from md_generator.codeflow.models.ir import EntryKind, FileParseResult
from md_generator.codeflow.parsers.treesitter_common import (
    append_import_edge,
    decode_text,
    load_language,
    mark_parse_errors,
    record_call,
    rel_key,
    sid,
)
from md_generator.codeflow.parsers.treesitter_entry_helpers import append_entry

logger = logging.getLogger(__name__)
_GRAMMAR_LABEL = "tree-sitter-ruby"

_HTTP_VERBS = frozenset(
    {"get", "post", "put", "patch", "delete", "head", "options", "match", "root"},
)
_RAILS_CONTROLLER_SUPERS = ("ApplicationController", "ActionController::Base", "ActionController")


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
        self.class_super: list[str] = []
        self.current_method: str | None = None
        self._entry_seen: set[str] = set()
        self._fp = str(path.resolve())

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
        super_n = node.child_by_field_name("superclass")
        super_txt = decode_text(self.source, super_n).strip() if super_n else ""
        self.class_stack.append(cname)
        self.class_super.append(super_txt)
        for ch in node.children:
            if ch.type == "class":
                self._visit_class(ch)
            elif ch.type in ("method", "singleton_method"):
                self._on_method(ch)
            else:
                self.visit(ch)
        self.class_stack.pop()
        self.class_super.pop()

    def _is_rails_controller(self) -> bool:
        if not self.class_stack:
            return False
        cname = self.class_stack[-1]
        if cname.endswith("Controller"):
            return True
        sup = self.class_super[-1] if self.class_super else ""
        return any(s in sup for s in _RAILS_CONTROLLER_SUPERS)

    def _is_action_cable_channel(self) -> bool:
        if not self.class_stack:
            return False
        cname = self.class_stack[-1]
        if not cname.endswith("Channel"):
            return False
        sup = self.class_super[-1] if self.class_super else ""
        return "Cable" in sup or "ApplicationCable" in sup

    def _on_method(self, node) -> None:  # noqa: ANN001
        name = node.child_by_field_name("name")
        if not name:
            return
        mname = decode_text(self.source, name).strip()
        fq = self.fq_class or None
        caller = sid(self.key, fq, mname)
        self.fr.symbol_ids.append(caller)
        line = node.start_point[0] + 1
        if self._is_rails_controller():
            append_entry(
                self.fr,
                seen=self._entry_seen,
                symbol_id=caller,
                label="Rails controller action",
                file_path=self._fp,
                line=line,
            )
        elif self._is_action_cable_channel() and mname in ("subscribed", "receive", "unsubscribed"):
            append_entry(
                self.fr,
                seen=self._entry_seen,
                symbol_id=caller,
                label=f"ActionCable {mname}",
                file_path=self._fp,
                line=line,
                kind=EntryKind.QUEUE,
            )
        prev = self.current_method
        self.current_method = caller
        for ch in node.children:
            self.visit(ch)
        self.current_method = prev

    def _call_has_block(self, node) -> bool:  # noqa: ANN001
        for ch in node.children:
            if ch.type == "block" or ch.type == "do_block":
                return True
        return False

    def _route_path_from_call(self, node) -> str | None:  # noqa: ANN001
        for ch in node.children:
            if ch.type == "argument_list":
                for arg in ch.children:
                    if arg.type == "string":
                        return decode_text(self.source, arg).strip().strip("\"'")
        return None

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
        line = node.start_point[0] + 1
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
                                    line=line,
                                )
                            return
        if not self.class_stack and callee in _HTTP_VERBS and self._call_has_block(node):
            route_path = self._route_path_from_call(node) or callee
            append_entry(
                self.fr,
                seen=self._entry_seen,
                symbol_id=sid(self.key, None, f"sinatra.{callee}.{route_path}"),
                label="Sinatra route",
                file_path=self._fp,
                line=line,
            )
        elif not self.class_stack and callee in _HTTP_VERBS and not self._call_has_block(node):
            route_path = self._route_path_from_call(node) or "route"
            append_entry(
                self.fr,
                seen=self._entry_seen,
                symbol_id=sid(self.key, None, f"routes.{callee}.{route_path}"),
                label=f"Rails route ({callee})",
                file_path=self._fp,
                line=line,
            )
        if not self.current_method:
            return
        record_call(
            self.fr,
            self.current_method,
            callee,
            line=line,
        )
