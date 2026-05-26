"""Read-only language capability matrix for CLI help and scan warnings (does not route parsing)."""

from __future__ import annotations

from typing import Any

# Keys are codeflow language ids (see lang_dispatch).
LANG_CAPABILITIES: dict[str, dict[str, Any]] = {
    "java": {
        "native_backend": "javalang",
        "treesitter_backend": "tree-sitter-java",
        "cfg": True,
        "spring_entries": True,
        "runtime_trace": False,
        "event_detection": True,
        "requires_external_tool_auto": False,
    },
    "python": {
        "native_backend": "ast",
        "treesitter_backend": "tree-sitter-python",
        "cfg": True,
        "spring_entries": False,
        "runtime_trace": True,
        "event_detection": True,
        "requires_external_tool_auto": False,
    },
    "javascript": {
        "native_backend": None,
        "treesitter_backend": "tree-sitter-javascript",
        "cfg": True,
        "spring_entries": False,
        "runtime_trace": False,
        "event_detection": True,
        "requires_external_tool_auto": False,
    },
    "typescript": {
        "native_backend": None,
        "treesitter_backend": "tree-sitter-typescript",
        "cfg": True,
        "spring_entries": False,
        "runtime_trace": False,
        "event_detection": True,
        "requires_external_tool_auto": False,
    },
    "tsx": {
        "native_backend": None,
        "treesitter_backend": "tree-sitter-typescript",
        "cfg": True,
        "spring_entries": False,
        "runtime_trace": False,
        "event_detection": True,
        "requires_external_tool_auto": False,
    },
    "cpp": {
        "native_backend": "libclang",
        "treesitter_backend": "tree-sitter-cpp",
        "cfg": True,
        "spring_entries": False,
        "runtime_trace": False,
        "event_detection": False,
        "requires_external_tool_auto": False,
    },
    "go": {
        "native_backend": "codeflow_go_dump",
        "treesitter_backend": "tree-sitter-go",
        "cfg": True,
        "spring_entries": False,
        "runtime_trace": False,
        "event_detection": False,
        "requires_external_tool_auto": True,
    },
    "php": {
        "native_backend": "codeflow_php_dump",
        "treesitter_backend": "tree-sitter-php",
        "cfg": True,
        "spring_entries": False,
        "runtime_trace": False,
        "event_detection": False,
        "requires_external_tool_auto": True,
    },
    "rust": {
        "native_backend": None,
        "treesitter_backend": "tree-sitter-rust",
        "cfg": True,
        "spring_entries": False,
        "runtime_trace": False,
        "event_detection": False,
        "requires_external_tool_auto": False,
        "imports": True,
        "calls": True,
        "entries": False,
    },
    "kotlin": {
        "native_backend": None,
        "treesitter_backend": "tree-sitter-kotlin",
        "cfg": True,
        "spring_entries": True,
        "runtime_trace": False,
        "event_detection": False,
        "requires_external_tool_auto": False,
        "imports": True,
        "calls": True,
        "entries": "partial",
    },
    "csharp": {
        "native_backend": None,
        "treesitter_backend": "tree-sitter-c-sharp",
        "cfg": True,
        "spring_entries": False,
        "runtime_trace": False,
        "event_detection": False,
        "requires_external_tool_auto": False,
        "imports": True,
        "calls": True,
        "entries": "partial",
    },
    "swift": {
        "native_backend": None,
        "treesitter_backend": "tree-sitter-swift",
        "cfg": True,
        "spring_entries": False,
        "runtime_trace": False,
        "event_detection": False,
        "requires_external_tool_auto": False,
        "imports": True,
        "calls": True,
        "entries": False,
    },
    "ruby": {
        "native_backend": None,
        "treesitter_backend": "tree-sitter-ruby",
        "cfg": True,
        "spring_entries": False,
        "runtime_trace": False,
        "event_detection": False,
        "requires_external_tool_auto": False,
        "imports": True,
        "calls": True,
        "entries": False,
    },
    "lua": {
        "native_backend": None,
        "treesitter_backend": "tree-sitter-lua",
        "cfg": True,
        "spring_entries": False,
        "runtime_trace": False,
        "event_detection": False,
        "requires_external_tool_auto": False,
        "imports": True,
        "calls": True,
        "entries": False,
    },
}


def capability_warnings(lang: str, *, parser_mode: str, emit_cfg: bool) -> list[str]:
    """Non-fatal warnings for scan-summary / verbose output."""
    cap = LANG_CAPABILITIES.get(lang)
    if not cap:
        return []
    out: list[str] = []
    if parser_mode == "treesitter" and not cap.get("treesitter_backend"):
        out.append(f"{lang}: --parser-mode treesitter is not defined for this language.")
    if emit_cfg and not cap.get("cfg"):
        out.append(f"{lang}: --emit-cfg is not supported for this language.")
    if parser_mode == "auto" and cap.get("requires_external_tool_auto"):
        out.append(
            f"{lang}: auto mode may need external tooling ({cap.get('native_backend')}); "
            f"use --parser-mode treesitter if tree-sitter grammar is installed.",
        )
    return out
