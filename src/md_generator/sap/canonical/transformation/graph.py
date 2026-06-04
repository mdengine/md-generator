from __future__ import annotations

from pydantic import BaseModel, Field

from md_generator.sap.canonical.transformation.node import TransformationNode


class TransformationGraph(BaseModel):
    graph_id: str
    root_node_id: str | None = None
    nodes: dict[str, TransformationNode] = Field(default_factory=dict)

    def add_node(self, node: TransformationNode) -> None:
        self.nodes[node.node_id] = node

    def topological_order(self) -> list[str]:
        indegree: dict[str, int] = {nid: 0 for nid in self.nodes}
        for node in self.nodes.values():
            for inp in node.inputs:
                if inp in indegree:
                    indegree[node.node_id] = indegree.get(node.node_id, 0) + 1
        queue = [nid for nid, deg in indegree.items() if deg == 0]
        order: list[str] = []
        while queue:
            nid = queue.pop(0)
            order.append(nid)
            node = self.nodes.get(nid)
            if not node:
                continue
            for out_id in node.outputs:
                if out_id not in self.nodes:
                    continue
                indegree[out_id] -= 1
                if indegree[out_id] == 0:
                    queue.append(out_id)
        if len(order) != len(self.nodes):
            return list(self.nodes.keys())
        return order
