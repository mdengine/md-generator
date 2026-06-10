from __future__ import annotations

from pathlib import Path

from md_generator.sap.canonical.bw.adso import BwAdso
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


class BwAdsoParser(SapParserPlugin):
    name = "bw.adso"
    version = "1.0.0"

    def capabilities(self) -> ParserCapability:
        return _bw_capabilities()

    def can_parse(self, path: Path) -> bool:
        return path.suffix.lower() == ".adso" or (path.suffix.lower() == ".json" and "adso" in path.name.lower())

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult | None:
        data = _read_json(path)
        name = data.get("name", path.stem)
        stable_id = f"BW::ADSO::{name}"
        fields = data.get("fields", [])
        src = BwSourceNode(node_id=f"adso:{name}", object_name=name, outputs=[])
        tg = _tg(f"tg:adso:{name}", "bw_adso", [src])
        g = _base_graph(stable_id, name, "BW::", "bw.adso")
        canonical = {
            "identity": _identity(stable_id, name, "BW::").model_dump(mode="json"),
            "provenance": _provenance(path, self.name).model_dump(mode="json"),
            "artifact_type": "bw.adso",
            "name": name,
            "package": data.get("package", "BW"),
            "source_path": str(path),
            "source_system": "bw",
            "artifact_hash": _provenance(path, self.name).source_checksum,
            "fields": fields,
            "transformation_graph": tg.model_dump(mode="json"),
            "transformation_graph_id": tg.graph_id,
            "graph_fragment_id": g.graph_id,
        }
        return _emit_bw_result(
            path,
            kind=SapObjectKind.BW_OBJECT,
            artifact_type="bw.adso",
            name=name,
            package=data.get("package", "BW"),
            namespace="BW::",
            canonical_model=BwAdso,
            canonical_data=canonical,
            graph=g,
            execution_semantic="bw_adso",
        )
