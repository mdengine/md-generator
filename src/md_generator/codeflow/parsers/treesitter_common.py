"""Shared Tree-sitter helpers for codeflow language parsers."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from md_generator.codeflow.graph.relations import REL_IMPORTS
from md_generator.codeflow.models.ir import CallResolution, CallSite, FileParseResult, StructuralEdge

logger = logging.getLogger(__name__)


def rel_key(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def decode_text(source: bytes, node: Any) -> str:
    if node is None:
        return ""
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def trim(s: str, max_len: int = 120) -> str:
    s = " ".join(s.split())
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def sid(key: str, cls: str | None, name: str) -> str:
    if cls:
        return f"{key}::{cls}.{name}"
    return f"{key}::{name}"


def call_resolution(callee: str) -> CallResolution:
    c = callee.strip().replace(" ", "")
    if not c:
        return "unknown"
    if c.isidentifier():
        return "static"
    if "." in c and all(part.isidentifier() for part in c.split(".") if part):
        return "static"
    return "dynamic"


def append_import_edge(fr: FileParseResult, file_key: str, import_path: str, *, line: int | None = None) -> None:
    raw = import_path.strip()
    if not raw:
        return
    fr.structural_edges.append(
        StructuralEdge(
            source_id=f"file:{file_key}",
            target_id=f"external::{raw}",
            relation=REL_IMPORTS,
            confidence=0.75,
            line=line,
        ),
    )


def record_call(
    fr: FileParseResult,
    caller: str,
    callee: str,
    *,
    line: int,
    condition_label: str | None = None,
) -> None:
    fr.calls.append(
        CallSite(
            caller_id=caller,
            callee_hint=callee,
            resolution=call_resolution(callee),
            is_async=False,
            line=line,
            condition_label=condition_label,
        ),
    )


def load_language(
    module_name: str,
    attr: str,
    *,
    package_label: str,
) -> tuple[Any, str] | None:
    """Return (Language, grammar_package label) or None if import fails."""
    try:
        mod = __import__(module_name, fromlist=[attr])
        lang_fn = getattr(mod, attr)
        lang = lang_fn() if callable(lang_fn) else lang_fn
        from tree_sitter import Language

        return Language(lang), package_label
    except ImportError as e:
        logger.debug("tree-sitter grammar unavailable %s: %s", package_label, e)
        return None


def walk_tree(root: Any, visit: Callable[[Any], None]) -> None:
    stack = [root]
    while stack:
        n = stack.pop()
        visit(n)
        for c in reversed(getattr(n, "children", []) or []):
            stack.append(c)


def annotation_simple_name(node: Any, source: bytes) -> str:
    """Best-effort simple name from marker_annotation / annotation node."""
    t = getattr(node, "type", "")
    if t == "marker_annotation":
        name = node.child_by_field_name("name")
        if name:
            return decode_text(source, name).strip().lstrip("@")
    if t == "annotation":
        name = node.child_by_field_name("name")
        if name:
            return decode_text(source, name).strip().lstrip("@")
    return trim(decode_text(source, node)).lstrip("@").split("(")[0].split()[0]


def function_body_node(node: Any) -> Any | None:
    """Kotlin/Rust-style function body (``function_body`` child or ``body`` field)."""
    body = node.child_by_field_name("body")
    if body is not None:
        return body
    for ch in getattr(node, "children", []) or []:
        if ch.type in ("function_body", "block"):
            return ch
    return None


def mark_parse_errors(fr: FileParseResult, root_node: Any, path: Path, *, language: str) -> None:
    """Record Tree-sitter syntax errors and log a warning; caller continues partial extraction."""
    if not getattr(root_node, "has_error", False):
        return
    fr.parse_had_errors = True
    logger.warning(
        "tree-sitter %s parse has errors (partial graph): %s",
        language,
        path,
    )
