from __future__ import annotations

import networkx as nx
from md_generator.codeflow.graph.multigraph_utils import CodeflowGraph
from md_generator.codeflow.graph.query import GraphQuery
from md_generator.codeflow.journey import JourneyBuilder, JourneyConfig, JourneyType


def test_journey_builder_methods() -> None:
    g = nx.MultiDiGraph()
    g.add_node("entry_node", type="entry", label="entry")
    g.add_node("class_node", type="class", label="class")
    g.add_node("file_node", type="file", label="file")
    
    g.add_edge("entry_node", "class_node", relation="CALLS")
    
    query = GraphQuery(g)
    cfg = JourneyConfig()
    builder = JourneyBuilder(query, g, cfg)
    
    # 1. API/Method Journey
    ir_method = builder.build_method_journey("entry_node")
    assert ir_method.metadata.journey_type == JourneyType.METHOD
    assert ir_method.root.id == "entry_node"
    
    # 2. Class Journey
    ir_class = builder.build_class_journey("class_node")
    assert ir_class.metadata.journey_type == JourneyType.CLASS
    assert ir_class.root.id == "class_node"
    
    # 3. File Journey
    ir_file = builder.build_file_journey("file_node")
    assert ir_file.metadata.journey_type == JourneyType.FILE
    assert ir_file.root.id == "file_node"


def test_journey_builder_forest() -> None:
    g = nx.MultiDiGraph()
    g.add_node("root1", type="entry", label="root1")
    g.add_node("root2", type="entry", label="root2")
    
    query = GraphQuery(g)
    cfg = JourneyConfig()
    builder = JourneyBuilder(query, g, cfg)
    
    forest = builder.build_forest(["root1", "root2"])
    assert forest.statistics.tree_count == 2
    assert len(forest.trees) == 2
    assert forest.trees[0].root.id == "root1"
    assert forest.trees[1].root.id == "root2"
