from __future__ import annotations

from pathlib import Path

from md_generator.sap.canonical.bw.composite_provider import BwCompositeProvider
from md_generator.sap.canonical.transformation.node import BwJoinNode, BwSourceNode
from md_generator.sap.framework.capabilities import ParserCapability
from md_generator.sap.graph.model import GraphEdge
from md_generator.sap.graph.taxonomy import RelationshipType
from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.parser.base import ParseContext, SapParseResult, SapParserPlugin
from md_generator.sap.parser.bw._common import (
    _base_graph,
    _bw_capabilities,
    _emit_bw_result,
    _identity,
    _provenance,
    _read_json,
    _tg,
)


class BwCompositeProviderParser(SapParserPlugin):
    name = "bw.composite_provider"
    version = "1.0.0"

    def capabilities(self) -> ParserCapability:
        return _bw_capabilities()

    def can_parse(self, path: Path) -> bool:
        return path.suffix.lower() in {".compositeprovider", ".cp"} or (
            path.suffix.lower() == ".json" and "composite" in path.name.lower()
        )

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult | None:
        data = _read_json(path)
        name = data.get("name", path.stem)
        members = data.get("members", [])
        stable_id = f"BW::CP::{name}"
        nodes = [BwJoinNode(node_id=f"join:{name}", join_type="union", inputs=[f"m:{m}" for m in members])]
        for m in members:
            nodes.append(BwSourceNode(node_id=f"m:{m}", object_name=m, outputs=[f"join:{name}"]))
        tg = _tg(f"tg:cp:{name}", "bw_composite", nodes)
        g = _base_graph(stable_id, name, "BW::", "bw.composite_provider")
        for m in members:
            mid = f"BW::{m}"
            g.add_edge(
                GraphEdge(
                    edge_id=f"{stable_id}->depends->{mid}",
                    source_id=stable_id,
                    target_id=mid,
                    relationship=RelationshipType.DEPENDS_ON,
                )
            )
        canonical = {
            "identity": _identity(stable_id, name, "BW::").model_dump(mode="json"),
            "provenance": _provenance(path, self.name).model_dump(mode="json"),
            "artifact_type": "bw.composite_provider",
            "name": name,
            "package": data.get("package", "BW"),
            "source_path": str(path),
            "source_system": "bw",
            "artifact_hash": _provenance(path, self.name).source_checksum,
            "members": members,
            "transformation_graph": tg.model_dump(mode="json"),
            "transformation_graph_id": tg.graph_id,
            "graph_fragment_id": g.graph_id,
        }
        return _emit_bw_result(
            path,
            kind=SapObjectKind.BW_OBJECT,
            artifact_type="bw.composite_provider",
            name=name,
            package=data.get("package", "BW"),
            namespace="BW::",
            canonical_model=BwCompositeProvider,
            canonical_data=canonical,
            graph=g,
            execution_semantic="bw_composite",
        )
