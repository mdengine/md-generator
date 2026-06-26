from __future__ import annotations

import networkx as nx
from md_generator.codeflow.graph.multigraph_utils import CodeflowGraph
from md_generator.codeflow.graph.query import GraphQuery
from md_generator.codeflow.journey import JourneyConfig, TraversalStrategy, SharedSubtreeMode
from md_generator.codeflow.journey.cache import JourneyCache
from md_generator.codeflow.journey.filters import EdgeFilter, ExpansionFilter, StopConditionEvaluator
from md_generator.codeflow.journey.traversal import traverse_journey


def test_dfs_and_bfs_traversal() -> None:
    # Build a simple multigraph
    # main -> service -> repo
    g = nx.MultiDiGraph()
    g.add_node("main", type="entry", language="python", label="main")
    g.add_node("service", type="method", language="python", label="service")
    g.add_node("repo", type="method", language="python", label="repo")
    
    g.add_edge("main", "service", relation="CALLS", confidence=1.0)
    g.add_edge("service", "repo", relation="CALLS", confidence=1.0)
    
    query = GraphQuery(g)
    cfg = JourneyConfig(traversal_strategy=TraversalStrategy.DFS)
    ef = EdgeFilter(cfg)
    exp = ExpansionFilter(cfg.expand_strategy)
    se = StopConditionEvaluator(cfg)
    cache = JourneyCache()
    
    # 1. DFS Traverse
    ir_dfs = traverse_journey(query, g, "main", cfg, ef, exp, se, cache)
    assert ir_dfs.root.id == "main"
    assert len(ir_dfs.root.children) == 1
    assert ir_dfs.root.children[0].id == "service"
    assert ir_dfs.root.children[0].children[0].id == "repo"
    assert ir_dfs.statistics.node_count == 3
    assert ir_dfs.statistics.maximum_depth == 2
    
    # 2. BFS Traverse
    cfg_bfs = JourneyConfig(traversal_strategy=TraversalStrategy.BFS)
    cache_bfs = JourneyCache()
    ir_bfs = traverse_journey(query, g, "main", cfg_bfs, ef, exp, se, cache_bfs)
    assert ir_bfs.root.id == "main"
    assert len(ir_bfs.root.children) == 1
    assert ir_bfs.root.children[0].id == "service"
    assert ir_bfs.root.children[0].children[0].id == "repo"
    assert ir_bfs.statistics.node_count == 3


def test_cycle_and_recursion_detection() -> None:
    g = nx.MultiDiGraph()
    # A -> B -> A (cycle)
    # A -> A (recursion)
    g.add_node("A", type="method", label="A")
    g.add_node("B", type="method", label="B")
    
    g.add_edge("A", "B", relation="CALLS")
    g.add_edge("B", "A", relation="CALLS")
    
    query = GraphQuery(g)
    cfg = JourneyConfig(max_depth=5)
    ef = EdgeFilter(cfg)
    exp = ExpansionFilter(cfg.expand_strategy)
    se = StopConditionEvaluator(cfg)
    cache = JourneyCache()
    
    ir = traverse_journey(query, g, "A", cfg, ef, exp, se, cache)
    
    # Check cycle node B -> A
    assert ir.root.id == "A"
    b_node = ir.root.children[0]
    assert b_node.id == "B"
    a_cycle = b_node.children[0]
    assert a_cycle.id == "A"
    assert a_cycle.is_cycle is True
    assert a_cycle.stop_reason.value == "cycle_detected"
    assert ir.statistics.cycle_count == 1
