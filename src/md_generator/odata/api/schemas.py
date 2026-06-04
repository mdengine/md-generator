from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from md_generator.odata.core.run_config import OdataRunConfig


class OdataGenerateOptions(BaseModel):
    graph: bool = False
    chunks: bool = False
    catalog: bool = True

    def to_partial_config(self) -> dict[str, Any]:
        return {
            "features": {
                "catalog": self.catalog,
                "graph": self.graph,
                "chunks": self.chunks,
            }
        }


def merge_upload_config(tmp_file: Path, options: OdataGenerateOptions | None) -> OdataRunConfig:
    from dataclasses import replace

    opts = options or OdataGenerateOptions()
    partial = opts.to_partial_config()
    feats = partial.get("features") or {}
    cfg = OdataRunConfig(file=tmp_file, output_path=Path(".")).normalized()
    return replace(
        cfg,
        features=replace(
            cfg.features,
            catalog=bool(feats.get("catalog", True)),
            graph=bool(feats.get("graph", False)),
            chunks=bool(feats.get("chunks", False)),
        ),
    )
