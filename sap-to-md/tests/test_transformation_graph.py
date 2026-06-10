from md_generator.sap.canonical.transformation.graph import TransformationGraph
from md_generator.sap.canonical.transformation.node import HanaJoinNode, HanaSourceNode


def test_transformation_graph_order():
    tg = TransformationGraph(graph_id="tg1")
    tg.add_node(HanaSourceNode(node_id="s1", object_name="T1", outputs=["j1"]))
    tg.add_node(HanaJoinNode(node_id="j1", inputs=["s1"], outputs=["out"]))
    order = tg.topological_order()
    assert "s1" in order
    assert "j1" in order
