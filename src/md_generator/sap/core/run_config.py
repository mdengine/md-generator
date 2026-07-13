from __future__ import annotations

import copy
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import yaml

from md_generator.sap.core.features import FEATURES


@dataclass
class PipelineSection:
    version: int = 1
    canonical_json: bool = True
    artifact_graph: bool = True
    rule_engine: bool = True
    openlineage_export: bool = False
    cross_lineage: bool = False
    semantic_chunks_jsonl: bool = False
    semantic_narrative: bool = False
    event_bus: bool = False


@dataclass
class ParserSection:
    plugins: list[str] = field(default_factory=list)
    include_abap: bool = True
    include_cds: bool = True
    include_ddic: bool = True
    include_odata: bool = True
    include_bapi: bool = True
    include_idoc: bool = True
    include_transport: bool = True
    include_hana: bool = True
    include_bw: bool = True
    include_datasphere: bool = True
    include_external: bool = False


@dataclass
class AnalyzerSection:
    lineage: bool = True
    governance: bool = True
    relationships: bool = True
    validations: bool = True
    authorization: bool = True
    semantics: bool = True


@dataclass
class ChunkingSection:
    enabled: bool = False
    types: list[str] = field(
        default_factory=lambda: ["entity", "relationship", "validation", "authorization", "lineage"]
    )


@dataclass
class GraphSection:
    enabled: bool = False
    mermaid: bool = True
    json_export: bool = True


@dataclass
class PerformanceSection:
    workers: int = 4
    cache_dir: str | None = None
    incremental: bool = True
    stream_threshold_mb: int = 5
    intelligence_list_cap: int = 80


@dataclass
class ODataSection:
    fetch_timeout_sec: int = 30
    verify_tls: bool = True
    cache_fetched: bool = True


@dataclass
class AbapJourneySection:
    max_depth: int = 1000
    expand_forms: bool = True
    expand_methods: bool = True
    expand_functions: bool = True
    expand_includes: bool = True
    expand_function_groups: bool = True
    stop_at_sap_standard: bool = True
    customer_namespaces: list[str] = field(default_factory=lambda: ["Z*", "Y*", "/COMPANY/*"])


@dataclass
class SapRunConfig:
    input_paths: list[Path] = field(default_factory=list)
    odata_urls: list[str] = field(default_factory=list)
    output_path: Path = field(default_factory=lambda: Path("output/sap-md"))
    split_files: bool = True
    include: frozenset[str] = field(default_factory=lambda: frozenset(FEATURES))
    exclude: frozenset[str] = field(default_factory=frozenset)
    parser: ParserSection = field(default_factory=ParserSection)
    odata: ODataSection = field(default_factory=ODataSection)
    analyzer: AnalyzerSection = field(default_factory=AnalyzerSection)
    chunking: ChunkingSection = field(default_factory=ChunkingSection)
    graph: GraphSection = field(default_factory=GraphSection)
    pipeline: PipelineSection = field(default_factory=PipelineSection)
    performance: PerformanceSection = field(default_factory=PerformanceSection)
    abap_journey: AbapJourneySection = field(default_factory=AbapJourneySection)
    write_manifest: bool = True
    markdown_cross_links: bool = True

    def normalized(self) -> SapRunConfig:
        workers = max(1, min(int(self.performance.workers), 64))
        cap = max(10, min(int(self.performance.intelligence_list_cap), 10_000))
        perf = replace(
            self.performance,
            workers=workers,
            intelligence_list_cap=cap,
            stream_threshold_mb=max(1, int(self.performance.stream_threshold_mb)),
        )
        paths = [Path(p).resolve() for p in self.input_paths if str(p).strip()]
        out = Path(self.output_path).resolve()
        return replace(self, input_paths=paths, output_path=out, performance=perf)

    def resolved_input_paths(self) -> list[Path]:
        return list(self.input_paths)

    def effective_features(self) -> frozenset[str]:
        return frozenset(f for f in self.include if f not in self.exclude)

    def with_output(self, path: Path) -> SapRunConfig:
        return replace(self, output_path=path)


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


def load_run_config(path: Path | None, overrides: dict[str, Any] | None = None) -> SapRunConfig:
    raw: dict[str, Any] = {}
    if path is not None and path.is_file():
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    else:
        try:
            import importlib.resources as ir

            txt = ir.files("md_generator.sap.config").joinpath("default.yaml").read_text(encoding="utf-8")
            raw = yaml.safe_load(txt) or {}
        except Exception:
            raw = {}
    if overrides:
        raw = _deep_merge(raw, overrides)

    inp = raw.get("input") or {}
    out = raw.get("output") or {}
    feats = raw.get("features") or {}
    include = frozenset(feats.get("include") or FEATURES)
    exclude = frozenset(feats.get("exclude") or [])
    paths = [Path(p) for p in (inp.get("paths") or [])]
    if not paths and inp.get("path"):
        paths = [Path(inp["path"])]
    odata_urls = list(inp.get("odata_urls") or [])

    perf_raw = raw.get("performance") or raw.get("execution") or {}
    odata_raw: dict[str, Any] = {}
    if isinstance(raw.get("parser"), dict):
        po = raw["parser"].get("odata")
        if isinstance(po, dict):
            odata_raw = {**odata_raw, **po}
    if isinstance(raw.get("odata"), dict):
        odata_raw = {**odata_raw, **raw["odata"]}
    return SapRunConfig(
        input_paths=paths,
        odata_urls=odata_urls,
        output_path=Path(out.get("path", "output/sap-md")),
        split_files=bool(out.get("split_files", True)),
        include=include,
        exclude=exclude,
        parser=_section(ParserSection, raw.get("parser")),
        odata=_section(ODataSection, odata_raw),
        analyzer=_section(AnalyzerSection, raw.get("analyzer")),
        chunking=_section(ChunkingSection, raw.get("chunking")),
        graph=_section(GraphSection, raw.get("graph")),
        pipeline=_section(PipelineSection, raw.get("pipeline")),
        performance=_section(PerformanceSection, perf_raw),
        abap_journey=_section(AbapJourneySection, raw.get("abap_journey")),
        write_manifest=bool(out.get("write_manifest", True)),
        markdown_cross_links=bool(out.get("markdown_cross_links", True)),
    )
