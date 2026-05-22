from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from md_generator.sap.core.run_config import SapRunConfig


@dataclass
class ExportManifestBuilder:
    counts: dict[str, int] = field(default_factory=dict)
    generated_files: list[str] = field(default_factory=list)
    graph_edges: int = 0

    def add_file(self, path: Path, output_root: Path) -> None:
        try:
            rel = path.resolve().relative_to(output_root.resolve()).as_posix()
        except ValueError:
            rel = path.name
        if rel not in self.generated_files:
            self.generated_files.append(rel)

    def bump(self, key: str, n: int = 1) -> None:
        self.counts[key] = self.counts.get(key, 0) + n

    def to_dict(self, cfg: SapRunConfig, *, metrics: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "included_features": sorted(cfg.effective_features()),
            "counts": dict(sorted(self.counts.items())),
            "graph_edges": self.graph_edges,
            "generated_files": sorted(self.generated_files),
            "metrics": metrics or {},
            "output": {
                "split_files": cfg.split_files,
                "write_manifest": cfg.write_manifest,
                "path": str(cfg.output_path),
            },
        }

    def write(self, output_root: Path, cfg: SapRunConfig, *, metrics: dict[str, Any] | None = None) -> Path:
        p = output_root / "export_manifest.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(cfg, metrics=metrics), indent=2), encoding="utf-8")
        return p
