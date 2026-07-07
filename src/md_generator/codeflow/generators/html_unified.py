from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from md_generator.codeflow.analyzers.flow_analyzer import FlowSlice
from md_generator.codeflow.enterprise_ir.base import GRAPH_SCHEMA_VERSION
from md_generator.codeflow.generators.cytoscape_enrich import enrich_graph_for_views


def _payload(
    graph_json: dict,
    entry_id: str,
    *,
    file_cluster_map: dict[str, int] | None = None,
    file_cluster_label_map: dict[str, str] | None = None,
) -> str:
    return json.dumps(
        enrich_graph_for_views(
            graph_json,
            entry_id,
            file_cluster_map=file_cluster_map,
            file_cluster_label_map=file_cluster_label_map,
        ),
        ensure_ascii=False,
    )


def write_html_unified(
    entry_dir: Path,
    entry_id: str,
    sl: FlowSlice,
    graph_json: dict,
    *,
    cfg_mermaid_text: str | None = None,
    semantic_neighbors: dict[str, Any] | None = None,
    search_hits: list[dict[str, Any]] | None = None,
    cluster_mode_note: str = "",
    semantic_search_results_href: str | None = None,
    nl_query_href: str | None = None,
    runtime_insights: dict[str, Any] | None = None,
    pr_impact: dict[str, Any] | None = None,
    cfg_by_symbol: dict[str, Any] | None = None,
    file_cluster_map: dict[str, int] | None = None,
    file_cluster_label_map: dict[str, str] | None = None,
) -> None:
    """Write ``index.unified.html`` under ``entry_dir``."""
    payload = _payload(
        graph_json,
        entry_id,
        file_cluster_map=file_cluster_map,
        file_cluster_label_map=file_cluster_label_map,
    )
    title = html.escape(entry_id)
    entry_json = json.dumps(entry_id, ensure_ascii=False)
    
    # Render dashboard structure
    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Enterprise Intelligence Dashboard — {title}</title>
  <script src="https://unpkg.com/cytoscape@3.26.0/dist/cytoscape.min.js"></script>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: system-ui, -apple-system, sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; background-color: #f8f9fa; }}
    header {{ background: #1f2937; color: white; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 3px solid #3b82f6; }}
    header h1 {{ font-size: 1.25rem; margin: 0; font-weight: 700; }}
    
    .stats-container {{ display: flex; gap: 12px; margin: 12px 20px; }}
    .card {{ background: white; border-radius: 8px; padding: 12px 16px; flex: 1; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid #3b82f6; }}
    .card h3 {{ margin: 0; font-size: 11px; text-transform: uppercase; color: #6b7280; letter-spacing: 0.05em; }}
    .card p {{ margin: 4px 0 0; font-size: 20px; font-weight: 700; color: #111827; }}

    .dashboard-tabs {{ display: flex; background: #e5e7eb; padding: 4px 20px 0; border-bottom: 1px solid #d1d5db; gap: 4px; }}
    .tab-btn {{ padding: 8px 16px; border: none; background: transparent; cursor: pointer; font-size: 13px; font-weight: 600; color: #4b5563; border-radius: 6px 6px 0 0; border: 1px solid transparent; border-bottom: none; }}
    .tab-btn:hover {{ background: #f3f4f6; }}
    .tab-btn.active {{ background: white; color: #2563eb; border-color: #d1d5db; position: relative; z-index: 1; }}

    main {{ flex: 1; display: flex; overflow: hidden; }}
    .tab-content {{ display: none; width: 100%; height: 100%; }}
    .tab-content.active {{ display: flex; }}

    .pane-side {{ width: 300px; border-right: 1px solid #e5e7eb; background: white; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 16px; }}
    .pane-main {{ flex: 1; position: relative; background: #fafafa; display: flex; flex-direction: column; }}

    .cy-canvas {{ width: 100%; height: 100%; }}
    
    .legend {{ position: absolute; bottom: 16px; right: 16px; background: white; padding: 12px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border: 1px solid #e5e7eb; font-size: 11px; z-index: 10; display: flex; flex-direction: column; gap: 6px; }}
    .legend-item {{ display: flex; align-items: center; gap: 8px; }}
    .legend-line {{ width: 24px; height: 3px; border-radius: 1px; }}

    .search-box {{ width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; outline: none; }}
    .search-box:focus {{ border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.2); }}

    table {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 12px; }}
    th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
    th {{ background: #f9fafb; font-weight: 600; color: #374151; }}
  </style>
</head>
<body>
  <header>
    <h1>Codeflow Enterprise Intelligence Dashboard</h1>
    <span style="font-size:12px;color:#9ca3af;">Schema Version: {GRAPH_SCHEMA_VERSION}</span>
  </header>

  <div class="stats-container">
    <div class="card" style="border-left-color: #3b82f6;">
      <h3>Scanned Files</h3>
      <p id="stat-files">0</p>
    </div>
    <div class="card" style="border-left-color: #10b981;">
      <h3>Dependencies</h3>
      <p id="stat-deps">0</p>
    </div>
    <div class="card" style="border-left-color: #f59e0b;">
      <h3>Configs</h3>
      <p id="stat-configs">0</p>
    </div>
    <div class="card" style="border-left-color: #ef4444;">
      <h3>Queries</h3>
      <p id="stat-queries">0</p>
    </div>
  </div>

  <div class="dashboard-tabs">
    <button class="tab-btn active" data-tab="graph">Graph Explorer</button>
    <button class="tab-btn" data-tab="lineage">Lineage Explorer</button>
    <button class="tab-btn" data-tab="config">Configuration Explorer</button>
    <button class="tab-btn" data-tab="dependency">Dependency Explorer</button>
    <button class="tab-btn" data-tab="database">Database Explorer</button>
  </div>

  <main>
    <!-- Graph Explorer -->
    <div class="tab-content active" id="tab-graph">
      <div class="pane-side">
        <input type="search" id="graph-search" class="search-box" placeholder="Filter nodes..."/>
        <div>
          <h4 style="margin:0 0 6px 0;">Selected Node</h4>
          <div id="graph-node-details" style="font-size:12px;background:#f3f4f6;padding:8px;border-radius:6px;min-height:60px;">
            Click a node to view properties.
          </div>
        </div>
      </div>
      <div class="pane-main">
        <div id="cy" class="cy-canvas"></div>
        <div class="legend">
          <div class="legend-item"><span class="legend-line" style="background:#3b82f6;"></span><span>CALLS (Solid Blue)</span></div>
          <div class="legend-item"><span class="legend-line" style="background:#10b981;border-style:dashed;"></span><span>USES_CONFIGURATION (Dashed Green)</span></div>
          <div class="legend-item"><span class="legend-line" style="background:#ef4444;"></span><span>READS_TABLE / WRITES_TABLE (Solid Red)</span></div>
          <div class="legend-item"><span class="legend-line" style="background:#9ca3af;border-style:dotted;"></span><span>IMPORTS (Dotted Gray)</span></div>
        </div>
      </div>
    </div>

    <!-- Lineage Explorer -->
    <div class="tab-content" id="tab-lineage">
      <div class="pane-side">
        <h4 style="margin:0 0 8px 0;">API-to-Database Lineage</h4>
        <p style="color:#6b7280;margin:0 0 12px 0;">Trace execution paths from REST entries down to columns and procedures.</p>
        <div id="lineage-list" style="display:flex;flex-direction:column;gap:8px;"></div>
      </div>
      <div class="pane-main" style="padding:20px;overflow-y:auto;">
        <h3>End-to-End Lineage Paths</h3>
        <table id="lineage-table">
          <thead>
            <tr>
              <th>Entry Endpoint</th>
              <th>Query Operation</th>
              <th>Target Table</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colspan="3" style="text-align:center;color:#6b7280;">Select a path to trace lineage details.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Configuration Explorer -->
    <div class="tab-content" id="tab-config">
      <div class="pane-main" style="padding:20px;overflow-y:auto;">
        <h3>Configuration Browser</h3>
        <input type="search" id="config-search" class="search-box" style="margin-bottom:16px;" placeholder="Search configurations..."/>
        <table id="config-table">
          <thead>
            <tr>
              <th>Configuration Key</th>
              <th>Value</th>
              <th>File</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>

    <!-- Dependency Explorer -->
    <div class="tab-content" id="tab-dependency">
      <div class="pane-main" style="padding:20px;overflow-y:auto;">
        <h3>Dependency Library Browser</h3>
        <input type="search" id="dep-search" class="search-box" style="margin-bottom:16px;" placeholder="Search dependencies..."/>
        <table id="dep-table">
          <thead>
            <tr>
              <th>Dependency Name</th>
              <th>Version</th>
              <th>Category</th>
              <th>Scope</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>

    <!-- Database Explorer -->
    <div class="tab-content" id="tab-database">
      <div class="pane-main" style="padding:20px;overflow-y:auto;">
        <h3>Database Table Browser</h3>
        <input type="search" id="db-search" class="search-box" style="margin-bottom:16px;" placeholder="Search tables..."/>
        <table id="db-table">
          <thead>
            <tr>
              <th>Table Name</th>
              <th>Database</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
  </main>

  <script>
    const DATA = {payload};
    const ENTRY = {entry_json};
    
    // Wire tab navigation
    document.querySelectorAll('.tab-btn').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        const tabId = 'tab-' + btn.getAttribute('data-tab');
        document.getElementById(tabId).classList.add('active');
        
        // Refresh cytoscape layout if graph tab
        if(btn.getAttribute('data-tab') === 'graph') {{
          window.dispatchEvent(new Event('resize'));
        }}
      }});
    }});

    // Prepopulate dashboard cards & tables
    const nodes = DATA.nodes || [];
    const edges = DATA.edges || [];

    const configs = nodes.filter(n => n.kind === 'CONFIG');
    const deps = nodes.filter(n => n.kind === 'DEPENDENCY');
    const tables = nodes.filter(n => n.kind === 'TABLE');
    const queries = nodes.filter(n => n.kind === 'QUERY');

    document.getElementById('stat-configs').textContent = configs.length;
    document.getElementById('stat-deps').textContent = deps.length;
    document.getElementById('stat-tables').textContent = tables.length;
    document.getElementById('stat-queries').textContent = queries.length;

    // Load configs table
    const configTbody = document.querySelector('#config-table tbody');
    configs.forEach(c => {{
      const tr = document.createElement('tr');
      tr.innerHTML = `<td><code>${{c.key || c.id}}</code></td><td>${{c.value || ''}}</td><td>${{c.file || ''}}</td><td>${{c.usage_status || 'Unused'}}</td>`;
      configTbody.appendChild(tr);
    }});

    // Load dependencies table
    const depTbody = document.querySelector('#dep-table tbody');
    deps.forEach(d => {{
      const tr = document.createElement('tr');
      tr.innerHTML = `<td><strong>${{d.name || d.id}}</strong></td><td>${{d.version || ''}}</td><td>${{d.dependency_type || 'External Library'}}</td><td>${{d.scope || 'compile'}}</td>`;
      depTbody.appendChild(tr);
    }});

    // Load database table
    const dbTbody = document.querySelector('#db-table tbody');
    tables.forEach(t => {{
      const tr = document.createElement('tr');
      tr.innerHTML = `<td><code>${{t.table_name || t.id}}</code></td><td>${{t.database_type || 'SQL'}}</td>`;
      dbTbody.appendChild(tr);
    }});

    // Initialize Cytoscape
    const els = [];
    nodes.forEach(n => {{
      els.push({{ data: {{ id: n.id, label: n.label || n.id, kind: n.kind }} }});
    }});
    edges.forEach(e => {{
      els.push({{ data: {{ id: e.source + '->' + e.target, source: e.source, target: e.target, edge_type: e.edge_type }} }});
    }});

    const cy = cytoscape({{
      container: document.getElementById('cy'),
      elements: els,
      style: [
        {{
          selector: 'node',
          style: {{
            label: 'data(label)',
            'font-size': 9,
            'text-wrap': 'wrap',
            'background-color': '#e5e7eb',
            'border-width': 1,
            'border-color': '#9ca3af',
            padding: '6px'
          }}
        }},
        {{ selector: 'node[kind="CONFIG"]', style: {{ 'background-color': '#fef3c7', 'border-color': '#f59e0b' }} }},
        {{ selector: 'node[kind="DEPENDENCY"]', style: {{ 'background-color': '#d1fae5', 'border-color': '#10b981' }} }},
        {{ selector: 'node[kind="TABLE"]', style: {{ 'background-color': '#fee2e2', 'border-color': '#ef4444' }} }},
        {{ selector: 'node[kind="QUERY"]', style: {{ 'background-color': '#ffedd5', 'border-color': '#f97316' }} }},
        {{
          selector: 'edge',
          style: {{
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'line-color': '#9ca3af',
            'target-arrow-color': '#9ca3af',
            width: 1.5
          }}
        }},
        {{ selector: 'edge[edge_type="CALLS"]', style: {{ 'line-color': '#3b82f6', 'target-arrow-color': '#3b82f6' }} }},
        {{ selector: 'edge[edge_type="USES_CONFIGURATION"]', style: {{ 'line-color': '#10b981', 'target-arrow-color': '#10b981', 'line-style': 'dashed' }} }},
        {{ selector: 'edge[edge_type="READS_TABLE"]', style: {{ 'line-color': '#ef4444', 'target-arrow-color': '#ef4444' }} }},
        {{ selector: 'edge[edge_type="WRITES_TABLE"]', style: {{ 'line-color': '#b91c1c', 'target-arrow-color': '#b91c1c' }} }}
      ],
      layout: {{ name: 'cose', animate: false }}
    }});

    // Cy node selection handler
    cy.on('tap', 'node', evt => {{
      const n = evt.target;
      const details = document.getElementById('graph-node-details');
      details.innerHTML = `<strong>ID:</strong> ${{n.id()}}<br><strong>Kind:</strong> ${{n.data('kind')}}`;
    }});
  </script>
</body>
</html>
"""
    (entry_dir / "index.unified.html").write_text(body, encoding="utf-8")
