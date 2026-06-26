"""Journey node / edge label formatting for output renderers.

Provides functions to produce human-readable labels from ``JourneyNodeIR``
nodes: symbol labels, edge annotations, CFG overlay blocks, and tree
indentation characters (``├──``, ``│``, ``└──``).
"""

from __future__ import annotations

from md_generator.codeflow.journey.ir import CfgOverlay, JourneyNodeIR


# ---------------------------------------------------------------------------
# Node labels
# ---------------------------------------------------------------------------

def format_node_label(node: JourneyNodeIR, *, show_language: bool = True) -> str:
    """Human-readable label: ``ClassName.methodName()  [Java]``."""
    parts: list[str] = [node.label]
    if show_language and node.language:
        parts.append(f"  [{node.language}]")
    return "".join(parts)


def format_node_suffix(node: JourneyNodeIR) -> str:
    """Extra info after the label: framework, line, confidence."""
    bits: list[str] = []
    if node.framework:
        bits.append(f"({node.framework})")
    if node.line is not None:
        bits.append(f"L{node.line}")
    if node.confidence < 1.0:
        bits.append(f"conf={node.confidence:.1f}")
    return " ".join(bits)


# ---------------------------------------------------------------------------
# Edge annotations
# ---------------------------------------------------------------------------

def format_edge_annotation(node: JourneyNodeIR) -> str:
    """``[CALLS]``, ``[async]``, ``→ if (condition)``."""
    parts: list[str] = []
    if node.edge_relation:
        parts.append(f"[{node.edge_relation}]")
    if node.call_type == "async":
        parts.append("[async]")
    if node.edge_label:
        parts.append(f"→ if ({node.edge_label})")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Stop / cycle annotations
# ---------------------------------------------------------------------------

def format_stop_reason(node: JourneyNodeIR) -> str:
    """Return a human-readable stop annotation or empty string."""
    if node.is_cycle:
        return "⟳ [cycle]"
    if node.is_recursive:
        return "⟳ [recursive]"
    if node.is_synthetic and "shared_ref" in node.annotations:
        return f"↳ see {node.annotations['shared_ref']} above"
    if node.is_collapsed and "collapsed_ref" in node.annotations:
        return "[… same as above]"
    if node.stop_reason is not None:
        return f"[stop: {node.stop_reason.value}]"
    return ""


# ---------------------------------------------------------------------------
# CFG overlay formatting (Improvement 12)
# ---------------------------------------------------------------------------

def format_cfg_overlay(cfg: CfgOverlay, indent: int = 0) -> list[str]:
    """Render a ``CfgOverlay`` tree as indented text lines.

    Example output::

        IF user == null
            throw AuthException()
        ELSE
            UserRepository.find()
                LOOP (retries < 3)
                    TRY
                        DBConnection.query()
                    CATCH TimeoutException
                        Thread.sleep()
                    FINALLY
                        Audit.log()
    """
    prefix = "    " * indent
    lines: list[str] = []

    if cfg.kind != "ROOT":
        lbl = cfg.kind
        if cfg.condition:
            lbl += f" {cfg.condition}"
        elif cfg.label:
            lbl += f" {cfg.label}"
        lines.append(f"{prefix}{lbl}")
    else:
        indent -= 1  # ROOT doesn't add a visible line

    for child in cfg.children:
        lines.extend(format_cfg_overlay(child, indent + 1))

    return lines


# ---------------------------------------------------------------------------
# Tree indentation
# ---------------------------------------------------------------------------

_PIPE = "│   "
_TEE = "├── "
_ELBOW = "└── "
_SPACE = "    "


def format_tree_lines(
    root: JourneyNodeIR,
    *,
    show_language: bool = True,
    show_edge: bool = True,
    show_stop: bool = True,
    show_cfg: bool = True,
) -> list[str]:
    """Produce indented tree lines with ``├──``/``└──`` characters.

    Returns a list of formatted strings ready for Markdown output.
    """
    lines: list[str] = []

    def _render(node: JourneyNodeIR, prefix: str, is_last: bool, is_root: bool) -> None:
        # Build connector
        if is_root:
            connector = ""
        else:
            connector = _ELBOW if is_last else _TEE

        # Build label
        label = format_node_label(node, show_language=show_language)
        suffix = format_node_suffix(node)
        edge_ann = format_edge_annotation(node) if show_edge and not is_root else ""
        stop_ann = format_stop_reason(node) if show_stop else ""

        parts = [p for p in [edge_ann, label, suffix, stop_ann] if p]
        line = f"{prefix}{connector}{' '.join(parts)}"
        lines.append(line)

        # CFG overlay (inline, indented under the node)
        if show_cfg and node.cfg_info is not None:
            cfg_indent = prefix + (_SPACE if is_last or is_root else _PIPE) + _SPACE
            cfg_lines = format_cfg_overlay(node.cfg_info)
            for cl in cfg_lines:
                lines.append(f"{cfg_indent}{cl}")

        # Recurse children
        child_prefix = prefix + (_SPACE if is_last or is_root else _PIPE)
        for i, child in enumerate(node.children):
            child_is_last = (i == len(node.children) - 1)
            _render(child, child_prefix, child_is_last, False)

    _render(root, "", True, True)
    return lines
