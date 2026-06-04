from __future__ import annotations

from pathlib import Path

from md_generator.sap.canonical.datasphere.view import DatasphereView
from md_generator.sap.canonical.transformation.node import HanaProjectionNode, HanaSourceNode
from md_generator.sap.framework.capabilities import ParserCapability
from md_generator.sap.graph.model import GraphEdge, GraphNode
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


class DatasphereViewParser(SapParserPlugin):
    name = "datasphere.view"
    version = "1.0.0"

    def capabilities(self) -> ParserCapability:
        return _ds_capabilities()

    def can_parse(self, path: Path) -> bool:
        n = path.name.lower()
        return path.suffix.lower() in {".dsview", ".view"} or (
            path.suffix.lower() == ".json" and ("dsview" in n or "ds_view" in n or "datasphere" in n)
        )

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult | None:
        data = _read_json(path)
        name = data.get("name", path.stem)
        source = data.get("source", "")
        cols = data.get("columns", [])
        stable_id = f"DATASPHERE::VIEW::{name}"
        src = HanaSourceNode(node_id=f"src:{source}", object_name=source, outputs=[f"proj:{name}"])
        proj = HanaProjectionNode(node_id=f"proj:{name}", inputs=[f"src:{source}"], properties={"columns": cols})
        tg = _tg(f"tg:view:{name}", "datasphere_view", [src, proj])
        g = _graph(stable_id, name, "datasphere.view")
        if source:
            tid = f"DS_SRC::{source}"
            g.add_node(GraphNode(node_id=tid, node_kind="dataset", label=source, namespace="DATASPHERE::"))
            g.add_edge(
                GraphEdge(
                    edge_id=f"{stable_id}->reads->{tid}",
                    source_id=stable_id,
                    target_id=tid,
                    relationship=RelationshipType.READS_FROM,
                )
            )
        canonical = {
            "identity": _identity(stable_id, name).model_dump(mode="json"),
            "provenance": _provenance(path, self.name).model_dump(mode="json"),
            "artifact_type": "datasphere.view",
            "name": name,
            "source_path": str(path),
            "artifact_hash": _provenance(path, self.name).source_checksum,
            "columns": cols,
            "transformation_graph": tg.model_dump(mode="json"),
            "graph_fragment_id": g.graph_id,
        }
        return _emit(
            path,
            kind=SapObjectKind.DATASPHERE_OBJECT,
            artifact_type="datasphere.view",
            name=name,
            model=DatasphereView,
            data=canonical,
            graph=g,
            sem="datasphere_view",
        )
