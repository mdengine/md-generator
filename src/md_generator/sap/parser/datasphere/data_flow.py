from __future__ import annotations

from pathlib import Path

from md_generator.sap.canonical.datasphere.data_flow import DatasphereDataFlow
from md_generator.sap.canonical.transformation.node import HanaFilterNode, HanaSourceNode
from md_generator.sap.framework.capabilities import ParserCapability
from md_generator.sap.graph.model import GraphEdge
from md_generator.sap.graph.taxonomy import RelationshipType
from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.parser.base import ParseContext, SapParseResult, SapParserPlugin
from md_generator.sap.parser.datasphere._common import (
    _ds_capabilities,
    _emit,
    _graph,
    _identity,
    _provenance,
    _read_json,
    _tg,
)


class DatasphereDataFlowParser(SapParserPlugin):
    name = "datasphere.data_flow"
    version = "1.0.0"

    def capabilities(self) -> ParserCapability:
        return _ds_capabilities()

    def can_parse(self, path: Path) -> bool:
        n = path.name.lower()
        return path.suffix.lower() in {".dataflow", ".df"} or (
            path.suffix.lower() == ".json" and ("dataflow" in n or "data_flow" in n)
        )

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult | None:
        data = _read_json(path)
        name = data.get("name", path.stem)
        steps = data.get("steps", [])
        stable_id = f"DATASPHERE::DF::{name}"
        nodes = []
        prev = None
        for i, step in enumerate(steps):
            sid = step.get("id", f"step{i}")
            if step.get("kind") == "source":
                nodes.append(HanaSourceNode(node_id=sid, object_name=step.get("object", ""), outputs=[f"next{i}"]))
            elif step.get("kind") == "filter":
                nodes.append(
                    HanaFilterNode(
                        node_id=sid,
                        inputs=[prev or ""],
                        expression=step.get("expression", ""),
                        outputs=[f"next{i}"],
                    )
                )
            prev = sid
        tg = _tg(f"tg:df:{name}", "datasphere_flow", nodes)
        g = _graph(stable_id, name, "datasphere.data_flow")
        for i, step in enumerate(steps):
            if i > 0:
                g.add_edge(
                    GraphEdge(
                        edge_id=f"{stable_id}->transforms->{step.get('id', i)}",
                        source_id=stable_id,
                        target_id=f"{stable_id}::{step.get('id', i)}",
                        relationship=RelationshipType.TRANSFORMS,
                    )
                )
        canonical = {
            "identity": _identity(stable_id, name).model_dump(mode="json"),
            "provenance": _provenance(path, self.name).model_dump(mode="json"),
            "artifact_type": "datasphere.data_flow",
            "name": name,
            "source_path": str(path),
            "artifact_hash": _provenance(path, self.name).source_checksum,
            "steps": steps,
            "transformation_graph": tg.model_dump(mode="json"),
            "graph_fragment_id": g.graph_id,
        }
        return _emit(
            path,
            kind=SapObjectKind.DATASPHERE_OBJECT,
            artifact_type="datasphere.data_flow",
            name=name,
            model=DatasphereDataFlow,
            data=canonical,
            graph=g,
            sem="datasphere_flow",
        )
