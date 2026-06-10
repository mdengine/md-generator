from __future__ import annotations

import copy
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ODataFetchSection:
    fetch_timeout_sec: int = 30
    verify_tls: bool = True
    cache_fetched: bool = True


@dataclass
class FeaturesSection:
    catalog: bool = True
    entities_json: bool = True
    graph: bool = False
    chunks: bool = False


@dataclass
class ChunkingSection:
    types: list[str] = field(
        default_factory=lambda: [
            "odata_service",
            "odata_entity_set",
            "odata_capabilities",
            "odata_index",
        ]
    )


@dataclass
class OdataRunConfig:
    file: Path | None = None
    folder: Path | None = None
    zip: Path | None = None
    urls: list[str] = field(default_factory=list)
    output_path: Path = field(default_factory=lambda: Path("output/odata-md"))
    write_manifest: bool = True
    features: FeaturesSection = field(default_factory=FeaturesSection)
    odata: ODataFetchSection = field(default_factory=ODataFetchSection)
    chunking: ChunkingSection = field(default_factory=ChunkingSection)

    def with_output(self, path: Path) -> OdataRunConfig:
        return replace(self, output_path=path)

    def normalized(self) -> OdataRunConfig:
        urls = [str(u).strip() for u in self.urls if str(u).strip()]
        timeout = max(5, min(int(self.odata.fetch_timeout_sec), 600))
        odata = replace(self.odata, fetch_timeout_sec=timeout)
        return replace(self, urls=urls, output_path=Path(self.output_path).resolve(), odata=odata)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def _section(cls: type, raw: dict[str, Any] | None) -> Any:
    raw = raw or {}
    fields = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
    return cls(**{k: v for k, v in raw.items() if k in fields})


def load_odata_run_config(path: Path | None, overrides: dict[str, Any] | None = None) -> OdataRunConfig:
    raw: dict[str, Any] = {}
    if path is not None and path.is_file():
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    else:
        try:
            import importlib.resources as ir

            txt = ir.files("md_generator.odata.config").joinpath("default.yaml").read_text(encoding="utf-8")
            raw = yaml.safe_load(txt) or {}
        except Exception:
            raw = {}
    if overrides:
        raw = _deep_merge(raw, overrides)

    inp = raw.get("input") or {}
    out = raw.get("output") or {}

    def _p(key: str) -> Path | None:
        v = inp.get(key)
        return Path(str(v)).expanduser() if v else None

    url_list = list(inp.get("urls") or [])
    if inp.get("url"):
        url_list.append(str(inp["url"]))

    return OdataRunConfig(
        file=_p("file"),
        folder=_p("folder"),
        zip=_p("zip"),
        urls=url_list,
        output_path=Path(str(out.get("path", "output/odata-md"))),
        write_manifest=bool(out.get("write_manifest", True)),
        features=_section(FeaturesSection, raw.get("features")),
        odata=_section(ODataFetchSection, raw.get("odata")),
        chunking=_section(ChunkingSection, raw.get("chunking")),
    ).normalized()
