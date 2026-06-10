from __future__ import annotations

import json
import logging
import shutil
from collections.abc import Callable
from pathlib import Path

from md_generator.odata.chunking.writer import write_odata_chunks
from md_generator.odata.core.run_config import OdataRunConfig
from md_generator.odata.fetch import infer_service_root
from md_generator.odata.generators.graph_builder import build_odata_graph, export_graph_json
from md_generator.odata.generators.mermaid_export import export_er_mermaid
from md_generator.odata.loaders.metadata_loader import load_odata_source
from md_generator.odata.models.domain import ODataMetadataDocument
from md_generator.odata.parser.registry import parse_document
from md_generator.odata.writers.catalog_writer import render_odata_catalog

logger = logging.getLogger(__name__)


def _emit(on_progress: Callable[[int, str], None] | None, pct: int, msg: str) -> None:
    if on_progress:
        on_progress(pct, msg)


def _merge_documents(docs: list[ODataMetadataDocument]) -> list[ODataMetadataDocument]:
    seen: dict[str, ODataMetadataDocument] = {}
    for doc in docs:
        key = doc.stable_id or doc.service_name
        seen[key] = doc
    return list(seen.values())


def extract_to_markdown(
    cfg: OdataRunConfig,
    *,
    on_progress: Callable[[int, str], None] | None = None,
    on_file: Callable[[Path], None] | None = None,
) -> list[ODataMetadataDocument]:
    cfg = cfg.normalized()
    root = Path(cfg.output_path)
    root.mkdir(parents=True, exist_ok=True)
    fetch_cache = root / ".odata-fetch"

    _emit(on_progress, 5, "load")
    loaded = load_odata_source(
        file=cfg.file,
        folder=cfg.folder,
        zip_path=cfg.zip,
        urls=cfg.urls,
        cache_dir=fetch_cache,
        fetch_timeout_sec=cfg.odata.fetch_timeout_sec,
    )

    _emit(on_progress, 20, "parse")
    documents: list[ODataMetadataDocument] = []
    for path in loaded.paths:
        doc = parse_document(path)
        if path in loaded.url_map:
            doc.metadata_url = loaded.url_map[path]
            doc.service_root = infer_service_root(loaded.url_map[path])
        documents.append(doc)
    documents = _merge_documents(documents)

    _emit(on_progress, 50, "catalog")
    if cfg.features.catalog:
        def _on_catalog_file(p: Path) -> None:
            if on_file:
                on_file(p)

        render_odata_catalog(root, documents, on_file=_on_catalog_file)

    if cfg.features.entities_json:
        json_dir = root / "json"
        json_dir.mkdir(parents=True, exist_ok=True)
        for doc in documents:
            p = json_dir / f"{doc.service_name}.json"
            p.write_text(json.dumps(doc.to_dict(), indent=2, default=str), encoding="utf-8")
            if on_file:
                on_file(p)

    if cfg.features.graph:
        _emit(on_progress, 70, "graph")
        graph = build_odata_graph(documents)
        export_graph_json(graph, root / "graph-full.json")
        if on_file:
            on_file(root / "graph-full.json")
        export_er_mermaid(graph, root / "graphs" / "relationships.mmd")
        if on_file:
            on_file(root / "graphs" / "relationships.mmd")

    if cfg.features.chunks:
        _emit(on_progress, 85, "chunks")
        for p in write_odata_chunks(root, documents, list(cfg.chunking.types)):
            if on_file:
                on_file(p)

    if cfg.write_manifest:
        manifest = {
            "documents": len(documents),
            "services": [d.service_name for d in documents],
            "features": {
                "catalog": cfg.features.catalog,
                "entities_json": cfg.features.entities_json,
                "graph": cfg.features.graph,
                "chunks": cfg.features.chunks,
            },
        }
        mp = root / "export_manifest.json"
        mp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        if on_file:
            on_file(mp)

    meta = root / "run_metadata.json"
    meta.write_text(
        json.dumps({"documents": len(documents), "output": str(root)}, indent=2),
        encoding="utf-8",
    )

    _emit(on_progress, 100, "done")

    for td in loaded.cleanup_dirs:
        try:
            shutil.rmtree(td, ignore_errors=True)
        except Exception:
            logger.debug("cleanup failed for %s", td, exc_info=True)

    return documents
