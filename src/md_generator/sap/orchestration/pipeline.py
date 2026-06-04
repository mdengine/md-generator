from __future__ import annotations

import hashlib
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

from md_generator.sap.analyzer.authorization.extractor import extract_authorization
from md_generator.sap.analyzer.governance.classifier import classify_objects
from md_generator.sap.analyzer.lineage.builder import build_lineage_metadata
from md_generator.sap.analyzer.relationships.engine import summarize_relationships
from md_generator.sap.analyzer.validation.extractor import extract_validations
from md_generator.sap.core.cache import ParseCache
from md_generator.sap.core.export_manifest import ExportManifestBuilder
from md_generator.sap.core.run_context import RunContext
from md_generator.sap.graph.builder import build_sap_graph
from md_generator.sap.graph.exporters.json_export import export_graph_json
from md_generator.sap.graph.exporters.mermaid_export import export_er_mermaid
from md_generator.sap.markdown.builders.writer import render_all
from md_generator.sap.markdown.chunking.writer import write_semantic_chunks
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.parser.base import ParseContext
from md_generator.sap.parser.discovery import discover_files
from md_generator.odata.fetch import fetch_metadata, infer_service_root
from md_generator.odata.parser.registry import parse_document
from md_generator.sap.parser.odata.parser import _is_odata_metadata
from md_generator.sap.parser.registry import default_registry

logger = logging.getLogger(__name__)


def _merge_objects(objects: list[SapObject]) -> list[SapObject]:
    seen: dict[str, SapObject] = {}
    for obj in objects:
        seen[obj.object_id] = obj
    return list(seen.values())


def _parse_one(
    path: Path,
    registry: object,
    ctx: ParseContext,
    cache: ParseCache,
) -> list[SapObject]:
    cached = cache.get(path)
    if cached and cached.get("objects"):
        return [_object_from_dict(o) for o in cached["objects"]]
    result = registry.parse_file(path, ctx)  # type: ignore[attr-defined]
    if not result:
        return []
    cache.put(path, {"objects": [_object_to_dict(o) for o in result.objects], "metadata": result.metadata})
    return result.objects


def _object_to_dict(obj: SapObject) -> dict:
    return {
        "kind": obj.kind.value,
        "name": obj.name,
        "package": obj.package,
        "description": obj.description,
        "source_path": str(obj.source_path) if obj.source_path else None,
        "raw_metadata": obj.raw_metadata,
        "semantic_entity": obj.semantic_entity,
        "tags": obj.tags,
        "category": obj.category.value,
        "is_catalog_object": obj.is_catalog_object,
    }


def _object_from_dict(d: dict) -> SapObject:
    from md_generator.sap.models.entities.kinds import SapObjectKind

    from md_generator.sap.models.metadata.odata import SapObjectCategory

    return SapObject(
        kind=SapObjectKind(d["kind"]),
        name=d["name"],
        package=d.get("package", ""),
        description=d.get("description", ""),
        source_path=Path(d["source_path"]) if d.get("source_path") else None,
        raw_metadata=d.get("raw_metadata", {}),
        semantic_entity=d.get("semantic_entity", ""),
        tags=d.get("tags", []),
        category=SapObjectCategory(d.get("category", SapObjectCategory.PHYSICAL.value)),
        is_catalog_object=bool(d.get("is_catalog_object", False)),
    )


def run_pipeline(
    ctx: RunContext,
    on_progress: Callable[[int, str], None] | None = None,
) -> None:
    cfg = ctx.config
    root = ctx.output_dir
    root.mkdir(parents=True, exist_ok=True)
    manifest = ExportManifestBuilder()

    def emit(pct: int, msg: str) -> None:
        if on_progress:
            on_progress(pct, msg)

    emit(5, "discover")
    fetch_cache = root / ".odata-fetch"
    extra_files: list[Path] = []
    url_map: dict[Path, str] = {}
    for url in cfg.odata_urls:
        try:
            p = fetch_metadata(url, fetch_cache, timeout=cfg.odata.fetch_timeout_sec)
            extra_files.append(p)
            url_map[p] = url
        except Exception as e:
            logger.warning("OData fetch failed for %s: %s", url, e)
    search_paths = list(cfg.input_paths) + extra_files
    files = discover_files(search_paths)
    ctx.metrics["files_discovered"] = len(files)

    registry = default_registry(cfg.parser)
    parse_ctx = ParseContext(root=ctx.input_paths[0] if ctx.input_paths else Path("."))
    cache_dir = Path(cfg.performance.cache_dir) if cfg.performance.cache_dir else root / ".cache"
    cache = ParseCache(cache_dir, enabled=cfg.performance.incremental)

    emit(10, "parse")
    all_objects: list[SapObject] = []
    workers = cfg.performance.workers
    if workers <= 1:
        for path in files:
            all_objects.extend(_parse_one(path, registry, parse_ctx, cache))
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(_parse_one, p, registry, parse_ctx, cache): p for p in files}
            done = 0
            for fut in as_completed(futs):
                all_objects.extend(fut.result())
                done += 1
                emit(10 + int(40 * done / max(len(futs), 1)), f"parse {done}/{len(futs)}")

    ctx.objects = _merge_objects(all_objects)
    ctx.metrics["objects_parsed"] = len(ctx.objects)

    for path in files:
        if _is_odata_metadata(path):
            doc = parse_document(path)
            if path in url_map:
                doc.metadata_url = url_map[path]
                doc.service_root = infer_service_root(url_map[path])
            ctx.odata_documents.append(doc)

    emit(55, "graph")
    graph = None
    if cfg.analyzer.relationships or cfg.graph.enabled:
        graph = build_sap_graph(ctx.objects)
        ctx.graph = graph
        manifest.graph_edges = graph.number_of_edges()

    emit(60, "analyze")
    validations = extract_validations(ctx.objects) if cfg.analyzer.validations else []
    auth_checks = extract_authorization(ctx.objects) if cfg.analyzer.authorization else []
    governance = classify_objects(ctx.objects) if cfg.analyzer.governance else []
    ctx.governance_fields = governance

    relationships = {}
    lineage = {}
    if graph is not None:
        relationships = summarize_relationships(graph, ctx.objects, cap=cfg.performance.intelligence_list_cap)
        if cfg.analyzer.lineage:
            lineage = build_lineage_metadata(ctx.objects, graph)

    emit(70, "markdown")
    render_all(
        root,
        ctx.objects,
        cfg,
        relationships=relationships,
        validations=validations,
        auth_checks=auth_checks,
        lineage=lineage,
        governance=governance,
        manifest=manifest,
        odata_documents=ctx.odata_documents,
    )

    if cfg.chunking.enabled and "chunks" in cfg.effective_features():
        chunk_types = list(cfg.chunking.types)
        if ctx.odata_documents and "odata_service" not in chunk_types:
            chunk_types.extend(["odata_service", "odata_entity_set", "odata_index"])
        cfg_hash = hashlib.sha256(json.dumps({"v": 1}, sort_keys=True).encode()).hexdigest()[:16]
        for p in write_semantic_chunks(
            root,
            ctx.objects,
            chunk_types,
            config_hash=cfg_hash,
            relationships=relationships,
            validations=validations,
            auth_checks=auth_checks,
            lineage=lineage,
            odata_documents=ctx.odata_documents,
        ):
            manifest.add_file(p, root)
        manifest.bump("chunks")

    if graph is not None and (cfg.graph.enabled or "graphs" in cfg.effective_features()):
        emit(85, "graphs")
        export_graph_json(graph, root / "graph-full.json")
        manifest.add_file(root / "graph-full.json", root)
        if cfg.graph.mermaid:
            export_er_mermaid(graph, root / "graphs" / "relationships.mmd")
            manifest.add_file(root / "graphs" / "relationships.mmd", root)

    emit(95, "manifest")
    if cfg.write_manifest:
        manifest.write(root, cfg, metrics=ctx.metrics)

    meta_path = root / "run_metadata.json"
    meta_path.write_text(
        json.dumps(
            {
                "objects": len(ctx.objects),
                "files": len(files),
                "metrics": ctx.metrics,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    manifest.add_file(meta_path, root)
    emit(100, "done")
