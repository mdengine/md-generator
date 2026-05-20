from __future__ import annotations

import argparse
import sys
from pathlib import Path

from md_generator.sap.core.extractor import extract_to_markdown
from md_generator.sap.core.features import FEATURES
from md_generator.sap.core.job_manager import SapJobManager
from md_generator.sap.core.run_config import SapRunConfig, load_run_config


def _parse_csv(s: str | None) -> frozenset[str] | None:
    if s is None or not s.strip():
        return None
    return frozenset(x.strip() for x in s.split(",") if x.strip())


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Export SAP artifacts to AI-ready Markdown.")
    p.add_argument("input", nargs="*", type=Path, help="SAP source paths (files or directories)")
    p.add_argument("--config", type=Path, default=None, help="Path to YAML config")
    p.add_argument("--output", type=Path, default=None, help="Output directory")
    p.add_argument("--include", default=None, help="Comma-separated feature list")
    p.add_argument("--exclude", default=None)
    p.add_argument("--include-cds", action="store_true", help="Enable CDS parser")
    p.add_argument("--include-ddic", action="store_true", help="Enable DDIC parser")
    p.add_argument("--include-lineage", action="store_true", help="Enable lineage analyzer")
    p.add_argument("--include-governance", action="store_true", help="Enable governance analyzer")
    p.add_argument("--graph", action="store_true", help="Export relationship graphs")
    p.add_argument("--chunk", action="store_true", help="Write semantic chunks")
    p.add_argument("--json-output", action="store_true", help="Include json_output feature")
    p.add_argument("--workers", type=int, default=None)
    p.add_argument("--async", dest="async_job", action="store_true", help="Run as background job")
    return p


def _apply_cli_overrides(cfg: SapRunConfig, ns: argparse.Namespace) -> SapRunConfig:
    from dataclasses import replace

    kw: dict = {}
    if ns.output:
        kw["output_path"] = ns.output
    if ns.input:
        kw["input_paths"] = list(ns.input)
    inc = _parse_csv(ns.include)
    if inc is not None:
        bad = inc - FEATURES
        if bad:
            raise SystemExit(f"Unknown features: {bad}")
        kw["include"] = inc
    exc = _parse_csv(ns.exclude)
    if exc is not None:
        kw["exclude"] = exc

    parser = cfg.parser
    analyzer = cfg.analyzer
    chunking = cfg.chunking
    graph = cfg.graph
    perf = cfg.performance

    if ns.include_cds:
        parser = replace(parser, include_cds=True)
    if ns.include_ddic:
        parser = replace(parser, include_ddic=True)
    if ns.include_lineage:
        analyzer = replace(analyzer, lineage=True)
    if ns.include_governance:
        analyzer = replace(analyzer, governance=True)
    if ns.graph:
        graph = replace(graph, enabled=True)
    if ns.chunk:
        chunking = replace(chunking, enabled=True)
    if ns.workers is not None:
        perf = replace(perf, workers=ns.workers)

    include = cfg.include
    if ns.json_output:
        include = frozenset(set(include) | {"json_output"})

    cfg = replace(cfg, parser=parser, analyzer=analyzer, chunking=chunking, graph=graph, performance=perf, **kw)
    if ns.json_output:
        cfg = replace(cfg, include=include)
    return cfg


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    ns = build_parser().parse_args(argv)
    overrides: dict = {}
    if ns.input:
        overrides.setdefault("input", {})["paths"] = [str(p) for p in ns.input]
    if ns.output:
        overrides.setdefault("output", {})["path"] = str(ns.output)
    if ns.include:
        overrides.setdefault("features", {})["include"] = list(_parse_csv(ns.include) or [])
    if ns.exclude:
        overrides.setdefault("features", {})["exclude"] = list(_parse_csv(ns.exclude) or [])
    if ns.chunk:
        overrides.setdefault("chunking", {})["enabled"] = True
    if ns.graph:
        overrides.setdefault("graph", {})["enabled"] = True
    if ns.workers is not None:
        overrides.setdefault("performance", {})["workers"] = ns.workers

    cfg = load_run_config(ns.config, overrides if overrides else None)
    cfg = _apply_cli_overrides(cfg, ns).normalized()

    if not cfg.input_paths:
        print("error: provide at least one input path", file=sys.stderr)
        return 2

    if ns.async_job:
        jm = SapJobManager()
        job_id = jm.enqueue(cfg)
        print(job_id)
        return 0

    extract_to_markdown(cfg)
    print(f"Wrote SAP knowledge pack to {cfg.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
