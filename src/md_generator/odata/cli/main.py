from __future__ import annotations

import argparse
import sys
from pathlib import Path

from md_generator.odata.core.extractor import extract_to_markdown
from md_generator.odata.core.run_config import OdataRunConfig, load_odata_run_config


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Export OData CSDL metadata to Markdown.")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate", help="Generate OData catalog Markdown")
    src = g.add_mutually_exclusive_group()
    src.add_argument("--file", type=Path, default=None, help="Path to metadata.xml/json")
    src.add_argument("--folder", type=Path, default=None, help="Directory containing OData metadata")
    src.add_argument("--zip", type=Path, default=None, help="ZIP archive containing metadata")
    g.add_argument("--url", action="append", default=[], help="Fetch $metadata from URL (repeatable)")
    g.add_argument("--config", type=Path, default=None, help="YAML config")
    g.add_argument("--output", type=Path, default=None, help="Output directory")
    g.add_argument("--graph", action="store_true", help="Export relationship graph")
    g.add_argument("--chunk", action="store_true", help="Write semantic chunks")
    return p


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    ns = build_parser().parse_args(argv)
    if ns.cmd != "generate":
        return 2

    overrides: dict = {}
    if ns.url:
        overrides.setdefault("input", {})["urls"] = list(ns.url)
    if ns.graph:
        overrides.setdefault("features", {})["graph"] = True
    if ns.chunk:
        overrides.setdefault("features", {})["chunks"] = True
        overrides.setdefault("chunking", {})["enabled"] = True

    cfg = load_odata_run_config(ns.config, overrides if overrides else None)
    kw: dict = {}
    if ns.file is not None:
        kw["file"] = ns.file
    if ns.folder is not None:
        kw["folder"] = ns.folder
    if ns.zip is not None:
        kw["zip"] = ns.zip
    if ns.url:
        kw["urls"] = list(ns.url)
    if ns.output is not None:
        kw["output_path"] = ns.output
    if ns.graph:
        from dataclasses import replace

        cfg = replace(cfg, features=replace(cfg.features, graph=True))
    if ns.chunk:
        from dataclasses import replace

        cfg = replace(cfg, features=replace(cfg.features, chunks=True))

    if kw:
        from dataclasses import replace

        cfg = replace(cfg, **kw)

    if not any((cfg.file, cfg.folder, cfg.zip, cfg.urls)):
        print("error: provide --file, --folder, --zip, or --url", file=sys.stderr)
        return 2

    extract_to_markdown(cfg)
    print(f"Wrote OData knowledge pack to {cfg.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
