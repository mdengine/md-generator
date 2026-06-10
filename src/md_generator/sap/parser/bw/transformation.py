from __future__ import annotations

from pathlib import Path

from md_generator.sap.canonical.bw.transformation import BwTransformation
from md_generator.sap.canonical.transformation.node import BwSourceNode, BwTransformNode
from md_generator.sap.framework.capabilities import ParserCapability
from md_generator.sap.graph.model import GraphEdge
from md_generator.sap.graph.taxonomy import RelationshipType
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


class BwTransformationParser(SapParserPlugin):
    name = "bw.transformation"
    version = "1.0.0"

    def capabilities(self) -> ParserCapability:
        return _bw_capabilities(sql="partial")

    def can_parse(self, path: Path) -> bool:
        return path.suffix.lower() == ".bwtr" or (
            path.suffix.lower() == ".json" and "transformation" in path.name.lower()
        )

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult | None:
        data = _read_json(path)
        name = data.get("name", path.stem)
        source = data.get("source", "")
        rules = data.get("rules", [])
        stable_id = f"BW::TR::{name}"
        src = BwSourceNode(node_id=f"src:{source}", object_name=source, outputs=[f"map:{name}"])
        tr = BwTransformNode(node_id=f"map:{name}", inputs=[f"src:{source}"], properties={"rules": rules})
        tg = _tg(f"tg:tr:{name}", "bw_transformation", [src, tr])
        g = _base_graph(stable_id, name, "BW::", "bw.transformation")
        if source:
            _add_reads(g, stable_id, source, source)
        for rule in rules:
            tgt_field = rule.get("target", "")
            if tgt_field:
                g.add_edge(
                    GraphEdge(
                        edge_id=f"{stable_id}->derives->{tgt_field}",
                        source_id=stable_id,
                        target_id=f"{stable_id}::{tgt_field}",
                        relationship=RelationshipType.DERIVES_FROM,
                        properties={"column": tgt_field, "source_field": rule.get("source", "")},
                    )
                )
        canonical = {
            "identity": _identity(stable_id, name, "BW::").model_dump(mode="json"),
            "provenance": _provenance(path, self.name).model_dump(mode="json"),
            "artifact_type": "bw.transformation",
            "name": name,
            "package": data.get("package", "BW"),
            "source_path": str(path),
            "source_system": "bw",
            "artifact_hash": _provenance(path, self.name).source_checksum,
            "rules": rules,
            "transformation_graph": tg.model_dump(mode="json"),
            "transformation_graph_id": tg.graph_id,
            "graph_fragment_id": g.graph_id,
        }
        return _emit_bw_result(
            path,
            kind=SapObjectKind.BW_OBJECT,
            artifact_type="bw.transformation",
            name=name,
            package=data.get("package", "BW"),
            namespace="BW::",
            canonical_model=BwTransformation,
            canonical_data=canonical,
            graph=g,
            execution_semantic="bw_transformation",
        )
