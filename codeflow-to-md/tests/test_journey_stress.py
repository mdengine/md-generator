from __future__ import annotations

import time
import networkx as nx
from md_generator.codeflow.graph.multigraph_utils import CodeflowGraph
from md_generator.codeflow.graph.query import GraphQuery
from md_generator.codeflow.journey import JourneyBuilder, JourneyConfig, TraversalStrategy


def test_stress_10k_nodes() -> None:
    # 10,000 nodes in a branching tree structure
    g = nx.MultiDiGraph()
    for i in range(10000):
        g.add_node(f"node_{i}", type="method", label=f"node_{i}")
        
    # Connect in a branching structure
    for i in range(1, 10000):
        parent = f"node_{(i - 1) // 3}"
        g.add_edge(parent, f"node_{i}", relation="CALLS")
        
    query = GraphQuery(g)
    cfg = JourneyConfig(max_depth=5, max_nodes=2000)
    builder = JourneyBuilder(query, g, cfg)
    
    start_time = time.time()
    ir = builder.build("node_0")
    duration = time.time() - start_time
    
    assert duration < 5.0  # Must be fast
    assert ir.statistics.node_count <= 2000


def test_stress_100k_nodes() -> None:
    # 100,000 nodes in a random tree
    g = nx.MultiDiGraph()
    for i in range(100000):
        g.add_node(f"node_{i}", type="method", label=f"node_{i}")
        
    for i in range(1, 100000):
        parent = f"node_{(i - 1) // 2}"
        g.add_edge(parent, f"node_{i}", relation="CALLS")
        
    query = GraphQuery(g)
    cfg = JourneyConfig(max_depth=8, max_nodes=1000)
    builder = JourneyBuilder(query, g, cfg)
    
    start_time = time.time()
    ir = builder.build("node_0")
    duration = time.time() - start_time
    
    assert duration < 10.0
    assert ir.statistics.node_count <= 1000


def test_stress_1m_edges() -> None:
    # Large graph with 10,000 nodes and 1,000,000 edges
    g = nx.MultiDiGraph()
    for i in range(10000):
        g.add_node(f"node_{i}", type="method", label=f"node_{i}")
        
    # Add dense edges
    for i in range(10000):
        for j in range(100):
            target = f"node_{(i * 101 + j) % 10000}"
            g.add_edge(f"node_{i}", target, relation="CALLS")
            
    query = GraphQuery(g)
    # Traversal should exit rapidly due to node limit or depth cap
    cfg = JourneyConfig(max_depth=5, max_nodes=1000)
    builder = JourneyBuilder(query, g, cfg)
    
    start_time = time.time()
    ir = builder.build("node_0")
    duration = time.time() - start_time
    
    assert duration < 10.0
    assert ir.statistics.node_count <= 1000
