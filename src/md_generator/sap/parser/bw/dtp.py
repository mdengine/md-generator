from __future__ import annotations

from pathlib import Path

from md_generator.sap.canonical.bw.dtp import BwDtp
from md_generator.sap.canonical.transformation.node import BwDtpNode, BwSourceNode
from md_generator.sap.framework.capabilities import ParserCapability
from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.parser.base import ParseContext, SapParseResult, SapParserPlugin
from md_generator.sap.parser.bw._common import (
    _add_reads,
    _base_graph,
    _bw_capabilities,
    _emit_bw_result,
    _identity,
    _provenance,
    _read_json,
    _tg,
)


class BwDtpParser(SapParserPlugin):
    name = "bw.dtp"
    version = "1.0.0"

    def capabilities(self) -> ParserCapability:
        return _bw_capabilities()

    def can_parse(self, path: Path) -> bool:
        return path.suffix.lower() == ".dtp" or (path.suffix.lower() == ".json" and "dtp" in path.name.lower())

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult | None:
        data = _read_json(path)
        name = data.get("name", path.stem)
        source = data.get("source", "")
        target = data.get("target", "")
        stable_id = f"BW::DTP::{name}"
        src_node = BwSourceNode(node_id=f"src:{source}", object_name=source, outputs=[f"dtp:{name}"])
        sink = BwDtpNode(node_id=f"dtp:{name}", inputs=[f"src:{source}"], target_name=target)
        tg = _tg(f"tg:dtp:{name}", "bw_dtp", [src_node, sink])
        g = _base_graph(stable_id, name, "BW::", "bw.dtp")
        if source:
            _add_reads(g, stable_id, source, source)
        if target:
            from md_generator.sap.graph.model import GraphEdge, GraphNode
            from md_generator.sap.graph.taxonomy import RelationshipType

            tid = f"BW::{target}"
            g.add_node(GraphNode(node_id=tid, node_kind="artifact", label=target, namespace="BW::"))
            g.add_edge(
                GraphEdge(
                    edge_id=f"{stable_id}->writes->{tid}",
                    source_id=stable_id,
                    target_id=tid,
                    relationship=RelationshipType.WRITES_TO,
                )
            )
        canonical = {
            "identity": _identity(stable_id, name, "BW::").model_dump(mode="json"),
            "provenance": _provenance(path, self.name).model_dump(mode="json"),
            "artifact_type": "bw.dtp",
            "name": name,
            "package": data.get("package", "BW"),
            "source_path": str(path),
            "source_system": "bw",
            "artifact_hash": _provenance(path, self.name).source_checksum,
            "source_name": source,
            "target_name": target,
            "transformation_graph": tg.model_dump(mode="json"),
            "transformation_graph_id": tg.graph_id,
            "graph_fragment_id": g.graph_id,
        }
        return _emit_bw_result(
            path,
            kind=SapObjectKind.BW_OBJECT,
            artifact_type="bw.dtp",
            name=name,
            package=data.get("package", "BW"),
            namespace="BW::",
            canonical_model=BwDtp,
            canonical_data=canonical,
            graph=g,
            execution_semantic="bw_dtp",
        )
