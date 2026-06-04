from __future__ import annotations

from pathlib import Path

from md_generator.sap.canonical.datasphere.analytical_model import DatasphereAnalyticalModel
from md_generator.sap.canonical.transformation.node import HanaSourceNode
from md_generator.sap.framework.capabilities import ParserCapability
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


class DatasphereAnalyticalModelParser(SapParserPlugin):
    name = "datasphere.analytical_model"
    version = "1.0.0"

    def capabilities(self) -> ParserCapability:
        return _ds_capabilities()

    def can_parse(self, path: Path) -> bool:
        return path.suffix.lower() in {".analyticalmodel", ".am"} or (
            path.suffix.lower() == ".json" and "analytical" in path.name.lower()
        )

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult | None:
        data = _read_json(path)
        name = data.get("name", path.stem)
        stable_id = f"DATASPHERE::AM::{name}"
        src = HanaSourceNode(node_id=f"src:{name}", object_name=name)
        tg = _tg(f"tg:am:{name}", "datasphere_analytical_model", [src])
        g = _graph(stable_id, name, "datasphere.analytical_model")
        canonical = {
            "identity": _identity(stable_id, name).model_dump(mode="json"),
            "provenance": _provenance(path, self.name).model_dump(mode="json"),
            "artifact_type": "datasphere.analytical_model",
            "name": name,
            "source_path": str(path),
            "artifact_hash": _provenance(path, self.name).source_checksum,
            "measures": data.get("measures", []),
            "transformation_graph": tg.model_dump(mode="json"),
            "graph_fragment_id": g.graph_id,
        }
        return _emit(
            path,
            kind=SapObjectKind.DATASPHERE_OBJECT,
            artifact_type="datasphere.analytical_model",
            name=name,
            model=DatasphereAnalyticalModel,
            data=canonical,
            graph=g,
            sem="datasphere_analytical_model",
        )
