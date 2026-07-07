from __future__ import annotations

import argparse
import datetime
import gc
import json
import os
import shutil
import sys
import time
import traceback
import subprocess
from pathlib import Path

# Add src/ to Python path
src_dir = str(Path(__file__).resolve().parent.parent / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

try:
    import psutil
except ImportError:
    psutil = None

import networkx as nx

# Import Codeflow internal modules
from md_generator.codeflow.core.run_config import ScanConfig
from md_generator.codeflow.ingestion.loader import LoadedWorkspace, collect_source_files
from md_generator.codeflow.lang_dispatch import lang_for_path, normalize_language_filter, should_parse_file_lang
from md_generator.codeflow.parsers.unified_parser import parse_source_file
from md_generator.codeflow.parsers.base import ParserRegistry, register_defaults
from md_generator.codeflow.parsers.ir_enrich import enrich_parse_results_with_ir
from md_generator.codeflow.plugins import global_plugin_registry
from md_generator.codeflow.plugins.registry import topological_sort_plugins
from md_generator.codeflow.enterprise_ir import EnterpriseIR, AnalysisStatistics, GRAPH_SCHEMA_VERSION, NodeType, EdgeType
from md_generator.codeflow.graph.enterprise_builder import EnterpriseGraphBuilder, generate_stable_uri
from md_generator.codeflow.graph.query import GraphQuery
from md_generator.codeflow.generators.enterprise_exporter import EnterpriseExporter
from md_generator.codeflow.graph.traversal import GraphTraversal
from md_generator.codeflow.repository.model import Repository


# Tiers configuration
TIERS = {
    "tiny": {"files": 100, "description": "Tiny (~1K files mock / 100 fast check)", "real_url": "https://github.com/pallets/flask.git"},
    "small": {"files": 1000, "description": "Small (~10K files mock / 1000 check)", "real_url": "https://github.com/django/django.git"},
    "medium": {"files": 5000, "description": "Medium (~50K files mock / 5000 check)", "real_url": "https://github.com/spring-projects/spring-framework.git"},
    "large": {"files": 10000, "description": "Large (~100K files mock / 10000 check)", "real_url": "https://github.com/kubernetes/kubernetes.git"},
    "enterprise": {"files": 25000, "description": "Enterprise (~250K files mock / 25000 check)", "real_url": "https://github.com/tensorflow/tensorflow.git"},
    "huge": {"files": 50000, "description": "Huge (~500K files mock / 50000 check)", "real_url": "https://github.com/torvalds/linux.git"}
}


class ResourceTracker:
    def __init__(self) -> None:
        self.process = psutil.Process(os.getpid()) if psutil else None
        self.start_time = 0.0
        self.start_mem = 0.0
        self.start_cpu = 0.0

    def start(self) -> None:
        gc.collect()
        self.start_time = time.perf_counter()
        if self.process:
            self.start_mem = self.process.memory_info().rss
            self.start_cpu = self.process.cpu_percent(interval=None)
        else:
            self.start_mem = float(sys.getsizeof(object()))

    def stop(self) -> tuple[float, float, float]:
        """Returns (duration_seconds, memory_delta_mb, cpu_percent)."""
        duration = time.perf_counter() - self.start_time
        if self.process:
            mem_delta = (self.process.memory_info().rss - self.start_mem) / (1024 * 1024)
            cpu_val = self.process.cpu_percent(interval=None)
        else:
            mem_delta = 0.0
            cpu_val = 0.0
        return duration, mem_delta, cpu_val


def get_current_rss_mb() -> float:
    if psutil:
        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    return 0.0


def generate_synthetic_repo(path: Path, num_files: int) -> int:
    """Generates a synthetic repository structure of the given file size count."""
    path.mkdir(parents=True, exist_ok=True)
    total_loc = 0
    
    # Generate mix of python, java, js/ts, go, config, sql files
    for i in range(num_files):
        ext_idx = i % 6
        file_num = i + 1
        if ext_idx == 0:
            # Python file
            filename = f"service_{file_num}.py"
            content = f"""# Python synthetic module
import os

class PythonService{file_num}:
    def __init__(self):
        self.config = os.getenv("CONFIG_VAR_{file_num}", "default")

    def handle_request(self, data):
        print("Handling request in PythonService{file_num}")
        self.save_data(data)

    def save_data(self, data):
        # sql query representation
        query = "INSERT INTO table_{file_num} (val) VALUES ('%s')" % data
        return query
"""
        elif ext_idx == 1:
            # Java file
            filename = f"Controller{file_num}.java"
            content = f"""package com.synthetic.app;

public class Controller{file_num} {{
    private String apiPath = "/api/v1/resource/{file_num}";

    public void processRequest() {{
        System.out.println("Processing request in Controller{file_num}");
        doService();
    }}

    private void doService() {{
        // calls database
        String sql = "SELECT * FROM users WHERE id = {file_num}";
    }}
}}
"""
        elif ext_idx == 2:
            # JS/TS file
            filename = f"component_{file_num}.ts"
            content = f"""// TypeScript component
export class Component{file_num} {{
    private url: string = "https://api.external.com/endpoint/{file_num}";
    
    public render(): void {{
        console.log("Rendering Component{file_num}");
        this.fetchData();
    }}
    
    private fetchData(): void {{
        fetch(this.url).then(r => r.json());
    }}
}}
"""
        elif ext_idx == 3:
            # Go file
            filename = f"handler_{file_num}.go"
            content = f"""package main

import "fmt"

type GoHandler{file_num} struct {{
	Port int
}}

func (h *GoHandler{file_num}) Serve() {{
	fmt.Println("Serving GoHandler on port", h.Port)
}}
"""
        elif ext_idx == 4:
            # Config file
            filename = f"config_{file_num}.properties"
            content = f"""# Properties config
app.name=SyntheticApp{file_num}
app.version=1.0.0
database.url=jdbc:mysql://localhost:3306/db_{file_num}
database.username=user{file_num}
database.password=secret_{file_num}
"""
        else:
            # SQL / other file
            filename = f"query_{file_num}.sql"
            content = f"""-- Database queries
SELECT * FROM table_{file_num} WHERE id = {file_num};
UPDATE settings SET val = 'active' WHERE key = 'status_{file_num}';
"""
        
        file_path = path / filename
        file_path.write_text(content, encoding="utf-8")
        total_loc += len(content.splitlines())
        
    return total_loc


def clone_real_repo(url: str, dest_path: Path) -> bool:
    """Clones a real repository from git."""
    if dest_path.exists() and any(dest_path.iterdir()):
        print(f"Repository already exists at {dest_path}", file=sys.stderr)
        return True
    print(f"Cloning {url} to {dest_path}...", file=sys.stderr)
    try:
        dest_path.mkdir(parents=True, exist_ok=True)
        # Using shallow clone for speed
        subprocess.run(["git", "clone", "--depth", "1", url, str(dest_path)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"Failed to clone {url}: {e}", file=sys.stderr)
        return False


def run_benchmark(tier_name: str, use_real_repo: bool, cache_dir: Path, output_dir: Path) -> dict[str, Any]:
    tier_info = TIERS[tier_name]
    repo_path = cache_dir / tier_name
    
    # 1. Setup repository
    print(f"\n=======================================================", file=sys.stderr)
    print(f"BENCHMARKING TIER: {tier_name.upper()} ({tier_info['description']})", file=sys.stderr)
    print(f"=======================================================", file=sys.stderr)
    
    cloned_ok = False
    if use_real_repo:
        cloned_ok = clone_real_repo(tier_info["real_url"], repo_path)
    
    total_loc = 0
    if not cloned_ok:
        print(f"Generating synthetic mock repository...", file=sys.stderr)
        if repo_path.exists():
            shutil.rmtree(repo_path)
        total_loc = generate_synthetic_repo(repo_path, tier_info["files"])
    else:
        # Calculate LOC for cloned repo
        print(f"Calculating LOC of cloned repository...", file=sys.stderr)
        for root, _, files in os.walk(repo_path):
            for file in files:
                if any(file.endswith(ext) for ext in [".py", ".java", ".js", ".ts", ".go", ".properties", ".sql"]):
                    try:
                        p = Path(root) / file
                        total_loc += len(p.read_text(encoding="utf-8", errors="replace").splitlines())
                    except Exception:
                        pass

    # Create scan configuration
    scan_out = output_dir / tier_name
    scan_out.mkdir(parents=True, exist_ok=True)
    
    cfg = ScanConfig(
        project_root=repo_path,
        output_path=scan_out,
        config_analysis=True,
        dependency_analysis=True,
        query_analysis=True,
        external_analysis=True,
        repository_analysis=True,
        classification_analysis=True,
        annotation_analysis=True,
        semantic_analysis=True,
    )
    
    tracker = ResourceTracker()
    results: dict[str, Any] = {
        "tier": tier_name,
        "mode": "real" if cloned_ok else "synthetic",
        "repository_url": tier_info["real_url"] if cloned_ok else "local_mock",
        "loc": total_loc,
        "pipeline_stages_ms": {},
        "memory_milestones_mb": {},
        "metrics": {}
    }
    
    # Milestone: Startup
    results["memory_milestones_mb"]["startup"] = get_current_rss_mb()
    
    # --- STAGE 1: Discovery & Language Detection ---
    tracker.start()
    ws_main = LoadedWorkspace(root=repo_path, cleanup_dir=None)
    files = collect_source_files(ws_main.root, cfg.languages)
    allowed = normalize_language_filter(cfg.languages)
    discovered_files = []
    for p in files:
        lang = lang_for_path(p)
        if should_parse_file_lang(lang, allowed):
            discovered_files.append((p, lang))
    dur, mem, cpu = tracker.stop()
    results["pipeline_stages_ms"]["repository_discovery"] = dur * 1000
    results["memory_milestones_mb"]["post_discovery"] = get_current_rss_mb()
    print(f"  [1/6] Discovered {len(discovered_files)} files in {dur*1000:.1f} ms", file=sys.stderr)
    
    # --- STAGE 2: Parsing ---
    tracker.start()
    reg = ParserRegistry()
    register_defaults(reg)
    parse_results = []
    parsed_loc = 0
    backend_counts = {}
    for p, lang in discovered_files:
        try:
            pr = parse_source_file(reg, p, ws_main.root, lang, cfg.parser_mode)
            if pr:
                parse_results.append(pr)
                parsed_loc += pr.loc
                backend_counts[pr.parse_backend] = backend_counts.get(pr.parse_backend, 0) + 1
        except Exception:
            pass
    dur, mem, cpu = tracker.stop()
    results["pipeline_stages_ms"]["parsing"] = dur * 1000
    results["memory_milestones_mb"]["post_parsing"] = get_current_rss_mb()
    results["metrics"]["parse_throughput"] = {
        "files_per_sec": len(discovered_files) / dur if dur > 0 else 0,
        "loc_per_sec": parsed_loc / dur if dur > 0 else 0,
        "backend_counts": backend_counts
    }
    print(f"  [2/6] Parsed {len(parse_results)} files ({parsed_loc} LOC) in {dur*1000:.1f} ms (Throughput: {results['metrics']['parse_throughput']['loc_per_sec']:.1f} LOC/sec)", file=sys.stderr)

    # --- STAGE 3: Normalization & EnterpriseIR ---
    tracker.start()
    enrich_parse_results_with_ir(parse_results, cfg, ws_main.root)
    
    from md_generator.codeflow.plugins import global_plugin_registry
    plugins_to_run = [
        global_plugin_registry.get_plugin("configuration"),
        global_plugin_registry.get_plugin("dependency"),
        global_plugin_registry.get_plugin("query"),
        global_plugin_registry.get_plugin("external"),
        global_plugin_registry.get_plugin("classification"),
        global_plugin_registry.get_plugin("annotation"),
        global_plugin_registry.get_plugin("semantic_plugin")
    ]
    plugins_to_run = [p for p in plugins_to_run if p is not None]
    plugins_to_run = topological_sort_plugins(plugins_to_run)
    
    combined_ir = EnterpriseIR()
    repo_obj = Repository(name="local", path=ws_main.root, workspace=ws_main)
    
    for p_class in plugins_to_run:
        plugin = p_class()
        try:
            p_files = plugin.discover(repo_obj)
            for f in p_files:
                if plugin.scan(f):
                    raw = plugin.extract(f)
                    norm = plugin.normalize(raw)
                    if plugin.validate(norm):
                        norm = plugin.post_process(norm)
                        ir = plugin.build_ir(norm)
                        combined_ir.configs.extend(ir.configs)
                        combined_ir.dependencies.extend(ir.dependencies)
                        combined_ir.queries.extend(ir.queries)
                        combined_ir.tables.extend(ir.tables)
                        combined_ir.columns.extend(ir.columns)
                        combined_ir.views.extend(ir.views)
                        combined_ir.resources.extend(ir.resources)
                        combined_ir.queues.extend(ir.queues)
                        combined_ir.storages.extend(ir.storages)
                        combined_ir.events.extend(ir.events)
        except Exception:
            pass
            
    dur, mem, cpu = tracker.stop()
    results["pipeline_stages_ms"]["normalization"] = dur * 1000
    results["memory_milestones_mb"]["post_normalization"] = get_current_rss_mb()
    print(f"  [3/6] Normalization & IR extraction completed in {dur*1000:.1f} ms", file=sys.stderr)

    # --- STAGE 4: Graph Building & Dedup ---
    tracker.start()
    g = nx.MultiDiGraph()
    builder = EnterpriseGraphBuilder(
        graph=g,
        scan_id=tier_name,
        repository="local",
        branch="main",
        commit="head"
    )
    
    # Call lifecycle hooks on builder
    builder.merge_ir(combined_ir)
    
    dur, mem, cpu = tracker.stop()
    results["pipeline_stages_ms"]["graph_building"] = dur * 1000
    results["memory_milestones_mb"]["post_graph_building"] = get_current_rss_mb()
    results["metrics"]["graph_stats"] = {
        "nodes_count": g.number_of_nodes(),
        "edges_count": g.number_of_edges(),
        "nodes_created": builder.nodes_created,
        "nodes_reused": builder.nodes_reused,
        "edges_created": builder.edges_created,
        "nodes_per_sec": builder.nodes_created / dur if dur > 0 else 0,
        "edges_per_sec": builder.edges_created / dur if dur > 0 else 0
    }
    print(f"  [4/6] Built graph with {g.number_of_nodes()} nodes and {g.number_of_edges()} edges in {dur*1000:.1f} ms (Throughput: {results['metrics']['graph_stats']['nodes_per_sec']:.1f} nodes/sec)", file=sys.stderr)

    # --- STAGE 5: Graph Algorithms ---
    tracker.start()
    
    # Profile traversals
    dfs_dur = 0.0
    bfs_dur = 0.0
    scc_dur = 0.0
    cycle_dur = 0.0
    path_dur = 0.0
    
    nodes_sample = list(g.nodes())[:50]  # sample up to 50 nodes
    
    # DFS & BFS profiling
    t_start = time.perf_counter()
    for n in nodes_sample:
        GraphTraversal.dfs(g, n)
    dfs_dur = (time.perf_counter() - t_start) * 1000
    
    t_start = time.perf_counter()
    for n in nodes_sample:
        GraphTraversal.bfs(g, n)
    bfs_dur = (time.perf_counter() - t_start) * 1000


    # SCC
    t_start = time.perf_counter()
    sccs = list(nx.strongly_connected_components(g))
    scc_dur = (time.perf_counter() - t_start) * 1000

    # Cycle Detection
    t_start = time.perf_counter()
    has_cycle = False
    try:
        nx.find_cycle(g)
        has_cycle = True
    except nx.NetworkXNoCycle:
        pass
    cycle_dur = (time.perf_counter() - t_start) * 1000

    # Shortest paths sample
    t_start = time.perf_counter()
    if len(nodes_sample) >= 2:
        for i in range(min(10, len(nodes_sample) - 1)):
            try:
                nx.shortest_path(g, nodes_sample[i], nodes_sample[i+1])
            except Exception:
                pass
    path_dur = (time.perf_counter() - t_start) * 1000

    dur, mem, cpu = tracker.stop()
    results["pipeline_stages_ms"]["graph_algorithms"] = dur * 1000
    results["memory_milestones_mb"]["post_graph_algorithms"] = get_current_rss_mb()
    results["metrics"]["algorithm_timings_ms"] = {
        "dfs_batch": dfs_dur,
        "bfs_batch": bfs_dur,
        "scc_detection": scc_dur,
        "cycle_detection": cycle_dur,
        "shortest_path_batch": path_dur
    }
    print(f"  [5/6] Evaluated Graph Algorithms (DFS, BFS, SCC, Cycle) in {dur*1000:.1f} ms", file=sys.stderr)

    # --- STAGE 6: Export Performance ---
    tracker.start()
    g_query = GraphQuery(g)
    exporter = EnterpriseExporter(g_query, scan_out)
    
    stats_payload = {
        "files_scanned": len(discovered_files),
        "files_skipped": 0,
        "files_failed": 0,
        "nodes_created": builder.nodes_created,
        "nodes_reused": builder.nodes_reused,
        "edges_created": builder.edges_created,
        "cache_hits": 0,
        "cache_misses": len(discovered_files),
        "execution_time_seconds": dur,
        "diagnostics": []
    }
    
    exporter.export_all(stats_payload)
    dur, mem, cpu = tracker.stop()
    results["pipeline_stages_ms"]["exporting"] = dur * 1000
    results["memory_milestones_mb"]["post_exporting"] = get_current_rss_mb()
    print(f"  [6/6] Exported all formats (Markdown, CSV, JSON, SQLite) in {dur*1000:.1f} ms", file=sys.stderr)
    
    # Calculate Total Execution Time
    total_ms = sum(results["pipeline_stages_ms"].values())
    results["total_execution_time_ms"] = total_ms
    print(f"Tier {tier_name} completed in {total_ms:.1f} ms (Peak memory RSS: {results['memory_milestones_mb']['post_exporting']:.1f} MB)\n", file=sys.stderr)
    
    # Cleanup workspace closing
    ws_main.close()
    
    return results


def main() -> int:
    p = argparse.ArgumentParser(description="Codeflow Benchmarking and Scale runner")
    p.add_argument("--tier", choices=["tiny", "small", "medium", "large", "enterprise", "huge", "all"], default="tiny")
    p.add_argument("--real", action="store_true", default=False, help="Clone real repositories instead of generating synthetic ones")
    p.add_argument("--cache-dir", type=Path, default=Path(".cache/benchmarks"))
    p.add_argument("--output-dir", type=Path, default=Path("artifacts/benchmarks"))
    args = p.parse_args()
    
    cache_dir = args.cache_dir.resolve()
    output_dir = args.output_dir.resolve()
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    selected_tiers = []
    if args.tier == "all":
        selected_tiers = list(TIERS.keys())
    else:
        selected_tiers = [args.tier]
        
    benchmark_runs = []
    
    for tier in selected_tiers:
        try:
            run_results = run_benchmark(tier, args.real, cache_dir, output_dir)
            benchmark_runs.append(run_results)
        except Exception as e:
            print(f"Error benchmarking tier {tier}: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            
    # Save the consolidated run outcomes to a JSON file
    results_file = output_dir / "benchmark-results.json"
    results_file.write_text(json.dumps({
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "psutil_available": psutil is not None,
        "runs": benchmark_runs
    }, indent=2), encoding="utf-8")
    
    # Generate the Markdown report
    generate_markdown_report(benchmark_runs, output_dir / "benchmark-report.md", args.real)
    print(f"Benchmark run completed. Results saved to {results_file} and {output_dir / 'benchmark-report.md'}", file=sys.stderr)
    return 0


def generate_markdown_report(runs: list[dict[str, Any]], report_path: Path, real_repos: bool) -> None:
    lines = [
        "# Codeflow Benchmarking & Scaling Report",
        "",
        f"**Date:** {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"**Repository Type:** {'Real Open Source' if real_repos else 'Generated Synthetic Mocks'}",
        "",
        "## Performance Overview",
        "",
        "| Tier | Files | LOC | Total Time (ms) | Peak RAM RSS (MB) | Nodes | Edges |",
        "| --- | --- | --- | --- | --- | --- | --- |"
    ]
    
    for run in runs:
        g_stats = run["metrics"].get("graph_stats", {})
        lines.append(
            f"| **{run['tier'].upper()}** | {run['metrics'].get('parse_throughput', {}).get('files_per_sec', 0) * (run['pipeline_stages_ms'].get('parsing', 0) / 1000):.0f} | "
            f"{run['loc']:,} | {run['total_execution_time_ms']:,.1f} | {run['memory_milestones_mb'].get('post_exporting', 0):.1f} | "
            f"{g_stats.get('nodes_count', 0):,} | {g_stats.get('edges_count', 0):,} |"
        )
        
    lines.append("")
    lines.append("## Pipeline Phase Breakdown (ms)")
    lines.append("")
    
    # Pipeline stages headers
    stage_names = ["repository_discovery", "parsing", "normalization", "graph_building", "graph_algorithms", "exporting"]
    headers = ["Tier"] + [s.replace("_", " ").title() for s in stage_names]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    for run in runs:
        stages_ms = run["pipeline_stages_ms"]
        row = [f"**{run['tier'].upper()}**"]
        for s in stage_names:
            row.append(f"{stages_ms.get(s, 0):,.1f}")
        lines.append("| " + " | ".join(row) + " |")
        
    lines.append("")
    lines.append("## Parser Throughput & Backend Efficiency")
    lines.append("")
    lines.append("| Tier | Files/sec | LOC/sec | Parser Backends |")
    lines.append("| --- | --- | --- | --- |")
    
    for run in runs:
        tp = run["metrics"].get("parse_throughput", {})
        backends = ", ".join(f"{k}: {v}" for k, v in tp.get("backend_counts", {}).items())
        lines.append(f"| **{run['tier'].upper()}** | {tp.get('files_per_sec', 0):,.1f} | {tp.get('loc_per_sec', 0):,.1f} | {backends or 'None'} |")
        
    lines.append("")
    lines.append("## Graph Builder & Dedup Operations")
    lines.append("")
    lines.append("| Tier | Nodes Created | Nodes Reused | Edges Created | Nodes/sec | Edges/sec |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    
    for run in runs:
        g_stats = run["metrics"].get("graph_stats", {})
        lines.append(
            f"| **{run['tier'].upper()}** | {g_stats.get('nodes_created', 0):,} | {g_stats.get('nodes_reused', 0):,} | "
            f"{g_stats.get('edges_created', 0):,} | {g_stats.get('nodes_per_sec', 0):,.1f} | {g_stats.get('edges_per_sec', 0):,.1f} |"
        )
        
    lines.append("")
    lines.append("## Graph Algorithm Execution Detail (ms)")
    lines.append("")
    lines.append("| Tier | DFS Batch (50 nodes) | BFS Batch (50 nodes) | SCC Detection | Cycle Detection | Shortest Path |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    
    for run in runs:
        alg = run["metrics"].get("algorithm_timings_ms", {})
        lines.append(
            f"| **{run['tier'].upper()}** | {alg.get('dfs_batch', 0):,.2f} | {alg.get('bfs_batch', 0):,.2f} | "
            f"{alg.get('scc_detection', 0):,.2f} | {alg.get('cycle_detection', 0):,.2f} | {alg.get('shortest_path_batch', 0):,.2f} |"
        )
        
    lines.append("")
    lines.append("## Hardware Resource Telemetry (Memory RSS Milestones in MB)")
    lines.append("")
    lines.append("| Tier | Startup | Post Discovery | Post Parsing | Post Normalization | Post Graph Building | Post Exporting (Peak) |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    
    for run in runs:
        mem = run["memory_milestones_mb"]
        lines.append(
            f"| **{run['tier'].upper()}** | {mem.get('startup', 0):.1f} | {mem.get('post_discovery', 0):.1f} | "
            f"{mem.get('post_parsing', 0):.1f} | {mem.get('post_normalization', 0):.1f} | {mem.get('post_graph_building', 0):.1f} | "
            f"{mem.get('post_exporting', 0):.1f} |"
        )
        
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
