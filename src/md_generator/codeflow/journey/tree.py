"""Tree manipulation utilities for ``JourneyNodeIR``.

Post-processing functions applied after traversal: collapse chains, prune,
shared subtree handling (Q5), flatten, inject CFG overlay (Improvement 12).
"""

from __future__ import annotations

from typing import Any

from md_generator.codeflow.journey.ir import CfgOverlay, JourneyNodeIR
from md_generator.codeflow.journey.models import SharedSubtreeMode


# ---------------------------------------------------------------------------
# Collapse linear chains
# ---------------------------------------------------------------------------

def collapse_linear_chains(root: JourneyNodeIR) -> JourneyNodeIR:
    """Fold single-child chains into their parent.

    A chain ``A → B → C`` where B has exactly one child becomes ``A → C`` with
    B marked ``is_collapsed=True`` and stored in ``annotations["collapsed_chain"]``.
    """
    def _fold(node: JourneyNodeIR) -> JourneyNodeIR:
        while len(node.children) == 1:
            child = node.children[0]
            if child.is_cycle or child.is_synthetic:
                break
            # Merge: adopt grandchildren
            collapsed_label = child.label
            node.annotations.setdefault("collapsed_chain", []).append(collapsed_label)
            child.is_collapsed = True
            node.children = child.children
            # Update children's parent_id
            for gc in node.children:
                gc.parent_id = node.id
        # Recurse into remaining children
        for i, child in enumerate(node.children):
            node.children[i] = _fold(child)
        node.is_leaf = len(node.children) == 0
        return node

    return _fold(root)


# ---------------------------------------------------------------------------
# Prune below depth
# ---------------------------------------------------------------------------

def prune_below_depth(root: JourneyNodeIR, max_depth: int) -> JourneyNodeIR:
    """Remove children beyond ``max_depth``.  When ``max_depth=0`` (unlimited), no pruning."""
    if max_depth == 0:
        return root

    def _prune(node: JourneyNodeIR) -> None:
        if node.depth >= max_depth:
            node.children = []
            node.is_leaf = True
            return
        for child in node.children:
            _prune(child)
        node.is_leaf = len(node.children) == 0

    _prune(root)
    return root


# ---------------------------------------------------------------------------
# Shared subtree handling (Q5)
# ---------------------------------------------------------------------------

def apply_shared_subtree_mode(
    root: JourneyNodeIR,
    mode: SharedSubtreeMode,
) -> JourneyNodeIR:
    """Post-process the tree according to the shared-subtree strategy.

    * ``REFERENCE`` — first occurrence is fully expanded; subsequent become
      reference nodes with ``is_synthetic=True`` and ``annotations["shared_ref"]``.
    * ``DUPLICATE`` — no-op; every occurrence stays as-is.
    * ``COLLAPSE`` — first occurrence expanded; subsequent become collapsed nodes
      labelled ``[… same as <label> above]``.
    """
    if mode == SharedSubtreeMode.DUPLICATE:
        return root

    seen: dict[str, str] = {}  # node.id → first branch_id

    def _walk(node: JourneyNodeIR) -> None:
        if node.id in seen and not node.is_root:
            if mode == SharedSubtreeMode.REFERENCE:
                node.is_synthetic = True
                node.annotations["shared_ref"] = seen[node.id]
                node.children = []
                node.is_leaf = True
            elif mode == SharedSubtreeMode.COLLAPSE:
                node.is_collapsed = True
                node.annotations["collapsed_ref"] = seen[node.id]
                node.children = []
                node.is_leaf = True
        else:
            seen[node.id] = node.branch_id
            for child in node.children:
                _walk(child)

    _walk(root)
    return root


def merge_shared_subtrees(root: JourneyNodeIR) -> dict[str, list[str]]:
    """Identify identical subtrees by node ID + children structure.

    Returns a mapping ``{node_id: [branch_id, ...]}`` where len > 1 means
    duplicate subtrees exist.  Internal helper for ``apply_shared_subtree_mode``.
    """
    occurrences: dict[str, list[str]] = {}

    def _walk(node: JourneyNodeIR) -> None:
        occurrences.setdefault(node.id, []).append(node.branch_id)
        for child in node.children:
            _walk(child)

    _walk(root)
    return {k: v for k, v in occurrences.items() if len(v) > 1}


# ---------------------------------------------------------------------------
# Flatten
# ---------------------------------------------------------------------------

def flatten_to_list(root: JourneyNodeIR) -> list[JourneyNodeIR]:
    """DFS-order flat list of all nodes in the tree."""
    result: list[JourneyNodeIR] = []

    def _walk(node: JourneyNodeIR) -> None:
        result.append(node)
        for child in node.children:
            _walk(child)

    _walk(root)
    return result


# ---------------------------------------------------------------------------
# Tree metrics
# ---------------------------------------------------------------------------

def count_nodes(root: JourneyNodeIR) -> int:
    total = 1
    for child in root.children:
        total += count_nodes(child)
    return total


def max_depth(root: JourneyNodeIR) -> int:
    if not root.children:
        return root.depth
    return max(max_depth(c) for c in root.children)


def find_cycles(root: JourneyNodeIR) -> list[JourneyNodeIR]:
    """All nodes flagged with ``is_cycle=True``."""
    result: list[JourneyNodeIR] = []

    def _walk(node: JourneyNodeIR) -> None:
        if node.is_cycle:
            result.append(node)
        for child in node.children:
            _walk(child)

    _walk(root)
    return result


def find_leaves(root: JourneyNodeIR) -> list[JourneyNodeIR]:
    result: list[JourneyNodeIR] = []

    def _walk(node: JourneyNodeIR) -> None:
        if node.is_leaf or not node.children:
            result.append(node)
        for child in node.children:
            _walk(child)

    _walk(root)
    return result


# ---------------------------------------------------------------------------
# CFG Overlay injection (Improvement 12)
# ---------------------------------------------------------------------------

def inject_cfg_overlay(
    root: JourneyNodeIR,
    ir_methods: dict[str, Any],
    cfg_builder: Any | None = None,
) -> None:
    """Enrich method nodes with CFG control-flow information.

    ``ir_methods`` maps ``method_name`` → parsed IR method data.
    ``cfg_builder`` is an optional ``build_cfg_from_ir`` callable.
    When available, the CFG blocks are converted to ``CfgOverlay`` trees.
    """
    if cfg_builder is None:
        return

    def _walk(node: JourneyNodeIR) -> None:
        if node.node_type in ("method", "function", "entry"):
            key = node.method_name or node.label
            ir_data = ir_methods.get(key)
            if ir_data is not None:
                try:
                    cfg = cfg_builder(ir_data)
                    if cfg and hasattr(cfg, "blocks"):
                        overlay_children: list[CfgOverlay] = []
                        for block in cfg.blocks:
                            kind = getattr(block, "kind", "STATEMENT")
                            cond = getattr(block, "condition", None)
                            lbl = getattr(block, "label", None)
                            overlay_children.append(CfgOverlay(kind=kind, condition=cond, label=lbl))
                        if overlay_children:
                            node.cfg_info = CfgOverlay(kind="ROOT", children=overlay_children)
                except Exception:
                    pass  # CFG is optional — never break the journey

        for child in node.children:
            _walk(child)

    _walk(root)
