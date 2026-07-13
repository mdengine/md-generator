from __future__ import annotations

from pathlib import Path
from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.markdown.builders.renderer_context import RendererContext
from md_generator.sap.abap_journey.loaders import SourceLoader, StatementCache
from md_generator.sap.abap_journey.resolver import SymbolRepository
from md_generator.sap.abap_journey.graph_builder import CallGraphBuilder
from md_generator.sap.abap_journey.journey_builder import JourneyBuilder
from md_generator.sap.abap_journey.cache import IncrementalCache
from md_generator.sap.abap_journey.renderers.markdown import MarkdownRenderer
from md_generator.sap.abap_journey.renderers.mermaid import MermaidRenderer
from md_generator.sap.abap_journey.renderers.json_renderer import JsonRenderer
from md_generator.sap.abap_journey.renderers.graphviz import GraphvizRenderer
from md_generator.sap.core.run_config import AbapJourneySection

def build_journey_and_call_graph(artifact: CanonicalArtifact, ctx: RendererContext) -> str:
    cfg = getattr(ctx, "config", None)
    config = getattr(cfg, "abap_journey", None) if cfg else None
    if not config:
        config = AbapJourneySection()

    artifacts_dict = {}
    if ctx.cross_link_registry:
        artifacts_dict = ctx.cross_link_registry.artifact_by_name

    loader = SourceLoader(artifacts_dict)
    cache = StatementCache()
    repo = SymbolRepository(loader, cache)

    # 1. Resolve paths
    source_path = Path(artifact.source_path) if artifact.source_path else None
    if not source_path or not source_path.exists():
        res = loader.load_source(artifact.name)
        if res:
            _, source_path = res

    # 2. Check incremental cache
    output_dir = getattr(ctx, "output_dir", None) or Path("output/sap-md")
    cache_dir = output_dir / ".journey-cache"
    inc_cache = IncrementalCache(cache_dir)
    
    graph = None
    if source_path:
        graph = inc_cache.get(source_path)

    # 3. Build graph if cache miss
    if not graph:
        graph = CallGraphBuilder.build_graph_for_program(
            artifact.name, repo, config, source_path
        )
        if source_path and graph.nodes:
            inc_cache.put(source_path, graph)

    # 4. Save optional graph exports
    slug = artifact.name.lower().replace(" ", "-").replace("/", "-").replace("::", "-")
    graphs_dir = output_dir / "abap" / "graphs"
    graphs_dir.mkdir(parents=True, exist_ok=True)

    try:
        (graphs_dir / f"{slug}.json").write_text(JsonRenderer.render(graph), encoding="utf-8")
        (graphs_dir / f"{slug}.mmd").write_text(MermaidRenderer.render(graph), encoding="utf-8")
        (graphs_dir / f"{slug}.dot").write_text(GraphvizRenderer.render(graph), encoding="utf-8")
    except Exception:
        pass

    # 5. Build phases and render Markdown
    phases = JourneyBuilder.build_phases(graph)
    return MarkdownRenderer.render(artifact.name, graph, phases)
