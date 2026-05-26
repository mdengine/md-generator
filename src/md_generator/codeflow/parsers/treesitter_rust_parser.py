"""Rust parsing via Tree-sitter (optional ``codeflow-treesitter`` extra)."""

from __future__ import annotations

import logging
import re
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
from md_generator.codeflow.parsers.treesitter_entry_helpers import append_entry

logger = logging.getLogger(__name__)
_GRAMMAR_LABEL = "tree-sitter-rust"

_ACTIX_ATTRS = frozenset({"get", "post", "put", "delete", "patch", "head", "options", "route"})
_AXUM_ROUTE_RE = re.compile(r"\.route\s*\(\s*['\"]([^'\"]+)['\"]")


def rust_language():
    return load_language("tree_sitter_rust", "language", package_label=_GRAMMAR_LABEL)


def _attribute_name(node, source: bytes) -> str:  # noqa: ANN001
    for ch in node.children:
        if ch.type == "attribute":
            raw = decode_text(source, ch).strip().lstrip("#").strip("[]")
            return raw.split("(")[0].split("::")[-1].strip("!").lower()
    path = node.child_by_field_name("path") or node.child_by_field_name("name")
    if path:
        raw = decode_text(source, path).strip()
        return raw.split("::")[-1].strip("!()").lower()
    raw = decode_text(source, node).strip().lstrip("#").strip("[]")
    return raw.split("(")[0].split("::")[-1].strip("!").lower()


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
        source_text = source.decode("utf-8", errors="replace")
        tree = Parser(lang).parse(source)
        mark_parse_errors(fr, tree.root_node, path, language=self.language)

        entry_seen: set[str] = set()
        fp = str(fr.path.resolve())
        impl_type: str | None = None
        current: str | None = None
        pending_attrs: list[str] = []

        def flush_attrs(fn_sid: str, line: int) -> None:
            nonlocal pending_attrs
            attrs = {a.lower() for a in pending_attrs}
            if attrs & _ACTIX_ATTRS:
                append_entry(
                    fr,
                    seen=entry_seen,
                    symbol_id=fn_sid,
                    label="Actix web route",
                    file_path=fp,
                    line=line,
                )
            pending_attrs = []

        def walk(n) -> None:  # noqa: ANN001
            nonlocal impl_type, current, pending_attrs
            t = n.type
            if t == "impl_item":
                ty = n.child_by_field_name("type")
                impl_type = decode_text(source, ty).strip() if ty else None
            elif t == "attribute_item":
                pending_attrs.append(_attribute_name(n, source))
                return
            elif t == "function_item":
                name = n.child_by_field_name("name")
                if name:
                    mname = decode_text(source, name).strip()
                    current = sid(key, impl_type, mname) if impl_type else sid(key, None, mname)
                    fr.symbol_ids.append(current)
                    line = n.start_point[0] + 1
                    flush_attrs(current, line)

                    def visit_body(node) -> None:  # noqa: ANN001
                        if node.type == "call_expression" and current:
                            fn = node.child_by_field_name("function")
                            callee = decode_text(source, fn).strip() if fn else "call"
                            record_call(fr, current, callee, line=node.start_point[0] + 1)
                            if ".route" in callee:
                                for m in _AXUM_ROUTE_RE.finditer(decode_text(source, node)):
                                    route_path = m.group(1)
                                    sid_ax = (
                                        sid(key, impl_type, f"axum.route.{route_path}")
                                        if impl_type
                                        else sid(key, None, f"axum.route.{route_path}")
                                    )
                                    append_entry(
                                        fr,
                                        seen=entry_seen,
                                        symbol_id=sid_ax,
                                        label=f"Axum route ({route_path})",
                                        file_path=fp,
                                        line=node.start_point[0] + 1,
                                    )
                        for ch in node.children:
                            visit_body(ch)

                    for ch in n.children:
                        visit_body(ch)
                return
            elif t == "use_declaration":
                arg = n.child_by_field_name("argument")
                if arg:
                    append_import_edge(
                        fr,
                        key,
                        decode_text(source, arg).strip(),
                        line=n.start_point[0] + 1,
                    )
            for ch in n.children:
                walk(ch)

        walk(tree.root_node)

        for m in _AXUM_ROUTE_RE.finditer(source_text):
            route_path = m.group(1)
            line = source_text[: m.start()].count("\n") + 1
            sid_ax = sid(key, None, f"axum.route.{route_path}")
            append_entry(
                fr,
                seen=entry_seen,
                symbol_id=sid_ax,
                label=f"Axum route ({route_path})",
                file_path=fp,
                line=line,
            )

        return fr
