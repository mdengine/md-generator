from __future__ import annotations

from pathlib import Path

from md_generator.sap.canonical.bw.info_object import BwInfoObject
from md_generator.sap.canonical.transformation.node import BwSourceNode
from md_generator.sap.framework.capabilities import ParserCapability
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


class BwInfoObjectParser(SapParserPlugin):
    name = "bw.info_object"
    version = "1.0.0"

    def capabilities(self) -> ParserCapability:
        return _bw_capabilities(sql="partial")

    def can_parse(self, path: Path) -> bool:
        return path.suffix.lower() == ".infoobject" or (
            path.suffix.lower() == ".json" and "infoobject" in path.name.lower()
        )

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult | None:
        data = _read_json(path)
        name = data.get("name", path.stem)
        stable_id = f"BW::IO::{name}"
        src = BwSourceNode(node_id=f"io:{name}", object_name=name, outputs=[])
        tg = _tg(f"tg:io:{name}", "bw_info_object", [src])
        g = _base_graph(stable_id, name, "BW::", "bw.info_object")
        canonical = {
            "identity": _identity(stable_id, name, "BW::").model_dump(mode="json"),
            "provenance": _provenance(path, self.name).model_dump(mode="json"),
            "artifact_type": "bw.info_object",
            "name": name,
            "package": data.get("package", "BW"),
            "source_path": str(path),
            "source_system": "bw",
            "artifact_hash": _provenance(path, self.name).source_checksum,
            "characteristics": data.get("characteristics", []),
            "key_figures": data.get("key_figures", []),
            "transformation_graph": tg.model_dump(mode="json"),
            "transformation_graph_id": tg.graph_id,
            "graph_fragment_id": g.graph_id,
        }
        return _emit_bw_result(
            path,
            kind=SapObjectKind.BW_OBJECT,
            artifact_type="bw.info_object",
            name=name,
            package=data.get("package", "BW"),
            namespace="BW::",
            canonical_model=BwInfoObject,
            canonical_data=canonical,
            graph=g,
            execution_semantic="bw_info_object",
        )
