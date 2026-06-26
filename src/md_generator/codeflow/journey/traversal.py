"""Journey traversal engine — DFS / BFS over the graph via GraphQuery.

The traversal **never** directly iterates NetworkX; it accesses the graph
through ``GraphQuery`` and the ``multigraph_utils`` edge helpers.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from md_generator.codeflow.graph.multigraph_utils import (
    CodeflowGraph,
    edge_data_dicts,
    iter_out_edges,
    parse_confidence,
)
from md_generator.codeflow.graph.query import GraphQuery
from md_generator.codeflow.journey.cache import JourneyCache
from md_generator.codeflow.journey.filters import EdgeFilter, ExpansionFilter, StopConditionEvaluator
from md_generator.codeflow.journey.ir import (
    JourneyEdgeIR,
    JourneyIR,
    JourneyMetadata,
    JourneyNodeIR,
    JourneyStatistics,
)
from md_generator.codeflow.journey.models import (
    JourneyConfig,
    SharedSubtreeMode,
    StopCondition,
    TraversalStrategy,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _node_label(node_id: str, data: dict[str, Any]) -> str:
    """Human-readable label derived from node attributes."""
    cn = data.get("class_name") or ""
    mn = data.get("method_name") or data.get("name") or ""
    if cn and mn:
        return f"{cn}.{mn}()"
    if mn:
        return f"{mn}()"
    fp = data.get("file_path") or ""
    if fp:
        parts = fp.replace("\\", "/").rsplit("/", 1)
        base = parts[-1] if parts else fp
        return f"{base}::{mn or node_id}"
    return str(node_id)


def _node_type(data: dict[str, Any]) -> str:
    return (data.get("type") or data.get("kind") or "method").lower()


def _call_type_for_edge(edge_data: dict[str, Any]) -> str | None:
    rel = edge_data.get("relation") or ""
    if rel in ("ASYNC", "CALLS_ASYNC") or edge_data.get("async") is True:
        return "async"
    if rel in ("CALLS", "CALLS_SYNC"):
        return "sync"
    return None


# ---------------------------------------------------------------------------
# DFS traversal
# ---------------------------------------------------------------------------

def _dfs_expand(
    g: CodeflowGraph,
    query: GraphQuery,
    node_id: str,
    depth: int,
    config: JourneyConfig,
    edge_filter: EdgeFilter,
    expansion_filter: ExpansionFilter,
    stop_evaluator: StopConditionEvaluator,
    cache: JourneyCache,
    ancestors: set[str],
    counter: list[int],   # [node_count, execution_order]
    edges_out: list[JourneyEdgeIR],
    cycle_nodes: set[str],
    parent_branch_id: str,
    parent_id: str | None,
    edge_data: dict[str, Any] | None,
    shared_seen: dict[str, str],  # node_id → branch_id of first occurrence
) -> JourneyNodeIR:
    """Recursively expand a node into a ``JourneyNodeIR`` sub-tree."""
    data = cache.get_node_attrs(node_id) or (dict(g.nodes[node_id]) if node_id in g else {})

    label = _node_label(node_id, data)
    ntype = _node_type(data)

    # Build the node
    node = JourneyNodeIR(
        id=node_id,
        label=label,
        node_type=ntype,
        language=data.get("language"),
        file_path=data.get("file_path"),
        class_name=data.get("class_name"),
        method_name=data.get("method_name") or data.get("name"),
        framework=data.get("framework"),
        line=data.get("line"),
        edge_relation=(edge_data.get("relation") or edge_data.get("kind")) if edge_data else None,
        edge_label=edge_data.get("condition") if edge_data else None,
        call_type=_call_type_for_edge(edge_data) if edge_data else None,
        confidence=parse_confidence(edge_data.get("confidence"), 1.0) if edge_data else 1.0,
        depth=depth,
        execution_order=counter[1],
        branch_id=parent_branch_id,
        parent_id=parent_id,
        is_root=(depth == 0),
    )
    counter[0] += 1
    counter[1] += 1

    # Cycle detection
    if node_id in ancestors:
        node.is_cycle = True
        node.stop_reason = StopCondition.CYCLE_DETECTED
        node.is_leaf = True
        cycle_nodes.add(node_id)
        return node

    # Recursion detection (self-call)
    if parent_id == node_id:
        node.is_recursive = True

    # Node cap
    if counter[0] >= config.max_nodes:
        node.stop_reason = StopCondition.MAX_NODES_REACHED
        node.is_leaf = True
        return node

    # Stop condition
    if depth > 0:  # Don't stop at root
        stop = stop_evaluator.should_stop(
            data, depth, ancestors, node_count=counter[0], confidence=node.confidence,
        )
        if stop is not None:
            node.stop_reason = stop
            node.is_leaf = True
            return node

    # Expansion filter (Q4)
    if depth > 0 and not expansion_filter.should_expand(data):
        node.stop_reason = StopCondition.FRAMEWORK  # closest semantic match
        node.is_leaf = True
        return node

    # Shared subtree (Q5)
    if config.shared_subtrees == SharedSubtreeMode.REFERENCE and node_id in shared_seen and depth > 0:
        node.is_synthetic = True
        node.annotations["shared_ref"] = shared_seen[node_id]
        node.is_leaf = True
        return node
    if config.shared_subtrees == SharedSubtreeMode.COLLAPSE and node_id in shared_seen and depth > 0:
        node.is_collapsed = True
        node.annotations["collapsed_ref"] = shared_seen[node_id]
        node.is_leaf = True
        return node

    # Mark first occurrence
    if node_id not in shared_seen:
        shared_seen[node_id] = node.branch_id

    # Check subtree cache
    cached = cache.get_subtree(node_id)
    if cached is not None and depth > 0 and config.shared_subtrees != SharedSubtreeMode.DUPLICATE:
        node.is_synthetic = True
        node.annotations["shared_ref"] = cached.branch_id
        node.is_leaf = True
        return node

    # Expand children
    ancestors.add(node_id)
    child_edges: list[tuple[str, dict[str, Any]]] = []

    # Use cached successors or compute
    cached_succs = cache.get_successors(node_id)
    if cached_succs is not None:
        for succ_id in cached_succs:
            for ed in edge_data_dicts(g, node_id, succ_id):
                source_data = data
                target_data = cache.get_node_attrs(succ_id) or (dict(g.nodes[succ_id]) if succ_id in g else {})
                if edge_filter.accept(source_data, target_data, ed):
                    child_edges.append((succ_id, ed))
    else:
        succ_list: list[str] = []
        for _u, v, _k, ed in iter_out_edges(g, node_id):
            v_str = str(v)
            succ_list.append(v_str)
            target_data = cache.get_node_attrs(v_str) or (dict(g.nodes[v]) if v in g else {})
            if edge_filter.accept(data, target_data, ed):
                child_edges.append((v_str, dict(ed)))
        cache.put_successors(node_id, succ_list)

    # Cap children
    child_edges = child_edges[: config.max_children]

    for idx, (child_id, ced) in enumerate(child_edges):
        if counter[0] >= config.max_nodes:
            break
        child_branch = f"{node.branch_id}.{idx}"

        # Record edge
        edges_out.append(JourneyEdgeIR(
            source_id=node_id,
            target_id=child_id,
            relation=ced.get("relation") or ced.get("kind") or "CALLS",
            label=ced.get("condition"),
            call_type=_call_type_for_edge(ced),
            confidence=parse_confidence(ced.get("confidence"), 1.0),
            is_async=ced.get("async") is True or (ced.get("relation") or "") in ("ASYNC", "CALLS_ASYNC"),
            is_cycle_edge=(child_id in ancestors),
        ))

        child_node = _dfs_expand(
            g, query, child_id, depth + 1, config,
            edge_filter, expansion_filter, stop_evaluator, cache,
            ancestors, counter, edges_out, cycle_nodes,
            child_branch, node_id, ced, shared_seen,
        )
        child_node.sibling_index = idx
        child_node.traversal_index = idx
        node.children.append(child_node)

    ancestors.discard(node_id)

    node.is_leaf = len(node.children) == 0
    if node.is_leaf and node.stop_reason is None and not node.is_cycle:
        node.stop_reason = StopCondition.LEAF_NODE

    # Cache the subtree for reuse
    if depth > 0:
        cache.put_subtree(node_id, node)

    return node


# ---------------------------------------------------------------------------
# BFS traversal
# ---------------------------------------------------------------------------

def _bfs_expand(
    g: CodeflowGraph,
    query: GraphQuery,
    start_id: str,
    config: JourneyConfig,
    edge_filter: EdgeFilter,
    expansion_filter: ExpansionFilter,
    stop_evaluator: StopConditionEvaluator,
    cache: JourneyCache,
    edges_out: list[JourneyEdgeIR],
    cycle_nodes: set[str],
    shared_seen: dict[str, str],
) -> JourneyNodeIR:
    """BFS expansion producing the same ``JourneyNodeIR`` tree as DFS."""
    data = cache.get_node_attrs(start_id) or (dict(g.nodes[start_id]) if start_id in g else {})
    root = JourneyNodeIR(
        id=start_id,
        label=_node_label(start_id, data),
        node_type=_node_type(data),
        language=data.get("language"),
        file_path=data.get("file_path"),
        class_name=data.get("class_name"),
        method_name=data.get("method_name") or data.get("name"),
        framework=data.get("framework"),
        line=data.get("line"),
        depth=0,
        execution_order=0,
        branch_id="0",
        is_root=True,
    )

    node_count = 1
    exec_order = 1
    queue: deque[tuple[JourneyNodeIR, set[str]]] = deque()
    queue.append((root, {start_id}))
    shared_seen[start_id] = "0"

    while queue:
        parent_node, path_set = queue.popleft()
        if node_count >= config.max_nodes:
            break

        parent_data = cache.get_node_attrs(parent_node.id) or {}
        child_edges: list[tuple[str, dict[str, Any]]] = []
        for _u, v, _k, ed in iter_out_edges(g, parent_node.id):
            v_str = str(v)
            target_data = cache.get_node_attrs(v_str) or (dict(g.nodes[v]) if v in g else {})
            if edge_filter.accept(parent_data, target_data, ed):
                child_edges.append((v_str, dict(ed)))

        child_edges = child_edges[: config.max_children]

        for idx, (child_id, ced) in enumerate(child_edges):
            if node_count >= config.max_nodes:
                break

            child_depth = parent_node.depth + 1
            child_branch = f"{parent_node.branch_id}.{idx}"
            c_data = cache.get_node_attrs(child_id) or (dict(g.nodes[child_id]) if child_id in g else {})

            is_cycle = child_id in path_set
            is_recursive = child_id == parent_node.id

            child_node = JourneyNodeIR(
                id=child_id,
                label=_node_label(child_id, c_data),
                node_type=_node_type(c_data),
                language=c_data.get("language"),
                file_path=c_data.get("file_path"),
                class_name=c_data.get("class_name"),
                method_name=c_data.get("method_name") or c_data.get("name"),
                framework=c_data.get("framework"),
                line=c_data.get("line"),
                edge_relation=ced.get("relation") or ced.get("kind"),
                edge_label=ced.get("condition"),
                call_type=_call_type_for_edge(ced),
                confidence=parse_confidence(ced.get("confidence"), 1.0),
                depth=child_depth,
                execution_order=exec_order,
                branch_id=child_branch,
                parent_id=parent_node.id,
                sibling_index=idx,
                traversal_index=idx,
                is_cycle=is_cycle,
                is_recursive=is_recursive,
            )
            node_count += 1
            exec_order += 1

            if is_cycle:
                child_node.stop_reason = StopCondition.CYCLE_DETECTED
                child_node.is_leaf = True
                cycle_nodes.add(child_id)
            elif config.effective_max_depth is not None and child_depth >= config.effective_max_depth:
                child_node.stop_reason = StopCondition.MAX_DEPTH_REACHED
                child_node.is_leaf = True
            elif not expansion_filter.should_expand(c_data):
                child_node.stop_reason = StopCondition.FRAMEWORK
                child_node.is_leaf = True
            elif config.shared_subtrees == SharedSubtreeMode.REFERENCE and child_id in shared_seen:
                child_node.is_synthetic = True
                child_node.annotations["shared_ref"] = shared_seen[child_id]
                child_node.is_leaf = True
            else:
                stop = stop_evaluator.should_stop(
                    c_data, child_depth, path_set, node_count=node_count,
                    confidence=child_node.confidence,
                )
                if stop is not None:
                    child_node.stop_reason = stop
                    child_node.is_leaf = True
                else:
                    # Enqueue for further expansion
                    new_path = path_set | {child_id}
                    queue.append((child_node, new_path))
                    if child_id not in shared_seen:
                        shared_seen[child_id] = child_branch

            edges_out.append(JourneyEdgeIR(
                source_id=parent_node.id,
                target_id=child_id,
                relation=ced.get("relation") or ced.get("kind") or "CALLS",
                label=ced.get("condition"),
                call_type=_call_type_for_edge(ced),
                confidence=child_node.confidence,
                is_async=ced.get("async") is True,
                is_cycle_edge=is_cycle,
            ))

            parent_node.children.append(child_node)

        parent_node.is_leaf = len(parent_node.children) == 0
        if parent_node.is_leaf and parent_node.stop_reason is None and not parent_node.is_cycle:
            parent_node.stop_reason = StopCondition.LEAF_NODE

    return root


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def traverse_journey(
    query: GraphQuery,
    g: CodeflowGraph,
    start_id: str,
    config: JourneyConfig,
    edge_filter: EdgeFilter,
    expansion_filter: ExpansionFilter,
    stop_evaluator: StopConditionEvaluator,
    cache: JourneyCache,
) -> JourneyIR:
    """Build a ``JourneyIR`` by traversing the graph from ``start_id``.

    Uses ``GraphQuery`` as the primary access layer (per spec).
    Supports DFS (default) and BFS via ``config.traversal_strategy``.
    """
    if start_id not in g:
        # Empty journey for missing node
        empty_root = JourneyNodeIR(id=start_id, label=start_id, node_type="unknown", is_leaf=True, is_root=True)
        return JourneyIR(root=empty_root)

    # Warm the graph-index cache
    if not cache.stats().get("graph_index_size"):
        cache.warm_graph_index(g)

    edges_out: list[JourneyEdgeIR] = []
    cycle_nodes: set[str] = set()
    shared_seen: dict[str, str] = {}

    if config.traversal_strategy == TraversalStrategy.BFS:
        root = _bfs_expand(
            g, query, start_id, config,
            edge_filter, expansion_filter, stop_evaluator, cache,
            edges_out, cycle_nodes, shared_seen,
        )
    else:
        counter = [0, 0]  # [node_count, execution_order]
        root = _dfs_expand(
            g, query, start_id, 0, config,
            edge_filter, expansion_filter, stop_evaluator, cache,
            set(), counter, edges_out, cycle_nodes,
            "0", None, None, shared_seen,
        )

    # Build metadata
    data = cache.get_node_attrs(start_id) or (dict(g.nodes[start_id]) if start_id in g else {})
    metadata = JourneyMetadata(
        journey_type=config.journey_type,
        entry_id=start_id,
        entry_label=_node_label(start_id, data),
        config=config,
        schema_version=config.schema_version,
        cycle_nodes=cycle_nodes,
    )

    ir = JourneyIR(
        root=root,
        metadata=metadata,
        edges=edges_out,
    )

    # Compute statistics
    from md_generator.codeflow.journey.statistics import compute_statistics
    ir.statistics = compute_statistics(ir)

    # Update metadata totals
    metadata.total_nodes = ir.statistics.node_count
    metadata.total_depth = ir.statistics.maximum_depth
    metadata.truncated = ir.statistics.truncation_count > 0

    return ir
