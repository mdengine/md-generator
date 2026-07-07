"""HTML interactive multi-view renderer for journeys.

Generates a single self-contained HTML page containing the journey data
and interactive views (Tree, Force-directed Graph, Timeline, Paths, Stats).
No external JS/CSS dependencies required.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from md_generator.codeflow.journey.ir import JourneyIR
from md_generator.codeflow.journey.forest import JourneyForest
from md_generator.codeflow.journey.json_export import journey_ir_to_dict, journey_forest_to_dict


def html_template(data_json: str, is_forest: bool = False) -> str:
    """HTML code template embedding the journey data."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Journey Generator Viewer</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-main: #0f172a;
      --bg-sidebar: #1e293b;
      --bg-card: #1e293b90;
      --border-color: #334155;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --accent-primary: #3b82f6;
      --accent-success: #10b981;
      --accent-warning: #f59e0b;
      --accent-error: #ef4444;
      --font-family: 'Outfit', sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}

    body.light-mode {{
      --bg-main: #f8fafc;
      --bg-sidebar: #f1f5f9;
      --bg-card: #ffffff90;
      --border-color: #cbd5e1;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --accent-primary: #1d4ed8;
      --accent-success: #047857;
      --accent-warning: #b45309;
      --accent-error: #b91c1c;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: var(--font-family);
      background-color: var(--bg-main);
      color: var(--text-main);
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      transition: background-color 0.3s, color 0.3s;
    }}

    header {{
      background: var(--bg-sidebar);
      border-bottom: 1px solid var(--border-color);
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      z-index: 10;
    }}

    header h1 {{
      font-size: 1.25rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .theme-toggle {{
      background: none;
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 6px 12px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.875rem;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .tabs {{
      display: flex;
      background: var(--bg-main);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 2px;
    }}

    .tabs button {{
      background: none;
      border: none;
      color: var(--text-muted);
      padding: 6px 16px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.875rem;
      font-weight: 500;
      transition: all 0.2s;
    }}

    .tabs button.active {{
      background: var(--accent-primary);
      color: white;
    }}

    .layout-container {{
      flex: 1;
      display: flex;
      min-height: 0;
    }}

    aside {{
      width: 320px;
      background: var(--bg-sidebar);
      border-right: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      gap: 20px;
      padding: 20px;
      overflow-y: auto;
    }}

    main-panel {{
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
      position: relative;
    }}

    .view-content {{
      flex: 1;
      display: none;
      overflow: auto;
      padding: 24px;
      position: relative;
    }}

    .view-content.active {{
      display: block;
    }}

    /* Filters Styles */
    .filter-group {{
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}

    .filter-group label {{
      font-size: 0.8125rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    .filter-group input, .filter-group select {{
      background: var(--bg-main);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 8px 12px;
      border-radius: 6px;
      outline: none;
      font-family: inherit;
    }}

    /* Tree View Styling */
    .tree-node-wrapper {{
      margin-left: 20px;
      border-left: 1px dashed var(--border-color);
      padding-left: 8px;
    }}

    .tree-node-header {{
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 8px;
      border-radius: 6px;
      cursor: pointer;
      user-select: none;
      transition: background-color 0.2s;
    }}

    .tree-node-header:hover {{
      background-color: var(--border-color);
    }}

    .tree-node-toggle {{
      width: 16px;
      height: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.75rem;
      color: var(--text-muted);
    }}

    .node-badge {{
      font-size: 0.75rem;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: var(--font-mono);
      font-weight: 500;
    }}

    .badge-java {{ background: #2b579a20; color: #2b579a; border: 1px solid #2b579a40; }}
    .badge-python {{ background: #30699820; color: #306998; border: 1px solid #30699840; }}
    .badge-go {{ background: #00add820; color: #00add8; border: 1px solid #00add840; }}
    .badge-ts {{ background: #007acc20; color: #007acc; border: 1px solid #007acc40; }}

    .node-label {{
      font-family: var(--font-mono);
      font-size: 0.875rem;
    }}

    .node-meta {{
      font-size: 0.75rem;
      color: var(--text-muted);
    }}

    /* Canvas Graph view */
    #graph-canvas-container {{
      width: 100%;
      height: 100%;
      position: relative;
      overflow: hidden;
      background: var(--bg-main);
    }}

    #graph-canvas {{
      width: 100%;
      height: 100%;
      display: block;
      cursor: grab;
    }}

    #graph-canvas:active {{
      cursor: grabbing;
    }}

    .canvas-controls {{
      position: absolute;
      bottom: 20px;
      right: 20px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    .canvas-controls button {{
      width: 36px;
      height: 36px;
      border-radius: 8px;
      background: var(--bg-sidebar);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.25rem;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}

    /* Right Sliding Details Panel */
    .details-panel {{
      position: absolute;
      top: 0;
      right: -360px;
      width: 350px;
      height: 100%;
      background: var(--bg-sidebar);
      border-left: 1px solid var(--border-color);
      box-shadow: -10px 0 20px -10px rgba(0,0,0,0.3);
      transition: right 0.3s ease;
      z-index: 100;
      display: flex;
      flex-direction: column;
      padding: 24px;
      gap: 16px;
    }}

    .details-panel.open {{
      right: 0;
    }}

    .details-panel-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--border-color);
      padding-bottom: 12px;
    }}

    .details-panel-close {{
      background: none;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      font-size: 1.25rem;
    }}

    /* Stats view */
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}

    .stats-card {{
      background: var(--bg-sidebar);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    .stats-card-value {{
      font-size: 2rem;
      font-weight: 700;
      color: var(--accent-primary);
    }}

    .stats-card-label {{
      font-size: 0.875rem;
      color: var(--text-muted);
      font-weight: 500;
    }}

    /* Timeline Styles */
    .timeline-container {{
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding-left: 20px;
      border-left: 2px solid var(--border-color);
      position: relative;
    }}

    .timeline-item {{
      background: var(--bg-sidebar);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 12px 16px;
      position: relative;
      cursor: pointer;
      transition: transform 0.2s;
    }}

    .timeline-item:hover {{
      transform: translateX(4px);
    }}

    .timeline-item::before {{
      content: '';
      position: absolute;
      left: -27px;
      top: 50%;
      transform: translateY(-50%);
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: var(--accent-primary);
      border: 2px solid var(--bg-main);
    }}

    /* Path list styles */
    .path-card {{
      background: var(--bg-sidebar);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 16px;
      margin-bottom: 16px;
      cursor: pointer;
    }}

    .path-card-title {{
      font-weight: 600;
      margin-bottom: 8px;
      color: var(--accent-primary);
    }}

    .path-flow-steps {{
      font-family: var(--font-mono);
      font-size: 0.8125rem;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 6px;
    }}

    .path-arrow {{
      color: var(--text-muted);
    }}

    /* Bookmark button */
    .bookmark-btn {{
      background: none;
      border: none;
      cursor: pointer;
      color: var(--text-muted);
      font-size: 1.1rem;
    }}
    .bookmark-btn.bookmarked {{
      color: var(--accent-warning);
    }}
  </style>
</head>
<body>

  <header>
    <h1>
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
      Journey Generator View
    </h1>
    
    <div class="tabs" id="main-tabs">
      <button class="active" data-tab="tree">Tree View</button>
      <button data-tab="graph">Graph View</button>
      <button data-tab="timeline">Timeline</button>
      <button data-tab="paths">Paths</button>
      <button data-tab="stats">Stats</button>
    </div>

    <div style="display: flex; gap: 8px;">
      <button class="theme-toggle" id="theme-btn">
        <span class="icon">☀</span> Theme
      </button>
    </div>
  </header>

  <div class="layout-container">
    <aside>
      <div class="filter-group">
        <label for="search-input">Search Node</label>
        <input type="search" id="search-input" placeholder="Search by name/file...">
      </div>

      <div class="filter-group">
        <label for="depth-slider">Max Depth (<span id="depth-val">All</span>)</label>
        <input type="range" id="depth-slider" min="1" max="15" value="15">
      </div>

      <div class="filter-group">
        <label for="lang-filter">Language</label>
        <select id="lang-filter">
          <option value="all">All Languages</option>
        </select>
      </div>

      <div class="filter-group">
        <label for="fw-filter">Framework</label>
        <select id="fw-filter">
          <option value="all">All Frameworks</option>
        </select>
      </div>

      <div style="margin-top: auto; border-top: 1px solid var(--border-color); padding-top: 16px;">
        <h4 style="font-size: 0.8125rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; margin-bottom: 10px;">Bookmarks</h4>
        <div id="bookmarks-list" style="display:flex; flex-direction:column; gap:8px; font-size:0.875rem;">
          <p style="color: var(--text-muted); font-style: italic;">No bookmarks starred yet.</p>
        </div>
      </div>
    </aside>

    <main-panel>
      <!-- Tree View Tab -->
      <div class="view-content active" id="view-tree">
        <div id="tree-container"></div>
      </div>

      <!-- Graph View Tab -->
      <div class="view-content" id="view-graph" style="padding: 0;">
        <div id="graph-canvas-container">
          <canvas id="graph-canvas"></canvas>
          <div class="canvas-controls">
            <button id="zoom-in">+</button>
            <button id="zoom-out">−</button>
            <button id="zoom-fit">⛶</button>
          </div>
        </div>
      </div>

      <!-- Timeline Tab -->
      <div class="view-content" id="view-timeline">
        <div class="timeline-container" id="timeline-container"></div>
      </div>

      <!-- Paths Tab -->
      <div class="view-content" id="view-paths">
        <div id="paths-container"></div>
      </div>

      <!-- Stats Tab -->
      <div class="view-content" id="view-stats">
        <div class="stats-grid" id="stats-grid"></div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
          <div class="stats-card">
            <h4>Node Distribution</h4>
            <div id="node-dist-chart" style="margin-top: 16px;"></div>
          </div>
          <div class="stats-card">
            <h4>Edge Distribution</h4>
            <div id="edge-dist-chart" style="margin-top: 16px;"></div>
          </div>
        </div>
      </div>

      <!-- Right Sliding Details Panel -->
      <div class="details-panel" id="details-panel">
        <div class="details-panel-header">
          <h3 id="details-title">Node Details</h3>
          <button class="details-panel-close" id="details-close">×</button>
        </div>
        <div id="details-content" style="display:flex; flex-direction:column; gap:12px; font-size:0.9rem; overflow-y:auto;">
          <!-- Node details will populate here -->
        </div>
      </div>
    </main-panel>
  </div>

  <script>
    const JOURNEY_DATA = {data_json};
    const IS_FOREST = {str(is_forest).lower()};
    
    // Core state management
    let state = {{
      currentJourney: IS_FOREST ? JOURNEY_DATA.trees[0] : JOURNEY_DATA,
      selectedNode: null,
      filters: {{
        search: '',
        maxDepth: 15,
        language: 'all',
        framework: 'all'
      }},
      bookmarks: JSON.parse(localStorage.getItem('journey_bookmarks') || '[]')
    }};

    // DOM selectors
    const themeBtn = document.getElementById('theme-btn');
    const searchInput = document.getElementById('search-input');
    const depthSlider = document.getElementById('depth-slider');
    const depthVal = document.getElementById('depth-val');
    const langFilter = document.getElementById('lang-filter');
    const fwFilter = document.getElementById('fw-filter');
    const treeContainer = document.getElementById('tree-container');
    const timelineContainer = document.getElementById('timeline-container');
    const pathsContainer = document.getElementById('paths-container');
    const statsGrid = document.getElementById('stats-grid');
    const bookmarksList = document.getElementById('bookmarks-list');
    const detailsPanel = document.getElementById('details-panel');
    const detailsContent = document.getElementById('details-content');
    const detailsClose = document.getElementById('details-close');
    
    // Tab switching
    document.querySelectorAll('#main-tabs button').forEach(button => {{
      button.addEventListener('click', () => {{
        document.querySelectorAll('#main-tabs button').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.view-content').forEach(v => v.classList.remove('active'));
        
        button.classList.add('active');
        const tab = button.getAttribute('data-tab');
        document.getElementById('view-' + tab).classList.add('active');
        
        if (tab === 'graph') {{
          initGraphView();
        }}
      }});
    }});

    // Theme toggling
    themeBtn.addEventListener('click', () => {{
      document.body.classList.toggle('light-mode');
    }});

    // Close details panel
    detailsClose.addEventListener('click', () => {{
      detailsPanel.classList.remove('open');
      state.selectedNode = null;
    }});

    // Flatten helper
    function getFlatNodes(root) {{
      const nodes = [];
      function walk(n) {{
        nodes.push(n);
        if (n.children) n.children.forEach(walk);
      }}
      walk(root);
      return nodes;
    }}

    // Node Type color coding for graph & badges
    function getLanguageClass(lang) {{
      if (!lang) return '';
      const l = lang.toLowerCase();
      if (l.includes('java')) return 'badge-java';
      if (l.includes('python')) return 'badge-python';
      if (l.includes('go')) return 'badge-go';
      if (l.includes('ts') || l.includes('js')) return 'badge-ts';
      return '';
    }}

    // Render tree view recursively
    function renderTree(node, container) {{
      const wrapper = document.createElement('div');
      wrapper.className = 'tree-node-wrapper';
      
      const header = document.createElement('div');
      header.className = 'tree-node-header';
      
      const toggle = document.createElement('span');
      toggle.className = 'tree-node-toggle';
      toggle.textContent = node.children && node.children.length ? '▼' : '•';
      
      const label = document.createElement('span');
      label.className = 'node-label';
      label.textContent = node.label;
      
      const langBadge = document.createElement('span');
      if (node.language) {{
        langBadge.className = 'node-badge ' + getLanguageClass(node.language);
        langBadge.textContent = node.language;
      }}
      
      header.appendChild(toggle);
      header.appendChild(label);
      if (node.language) header.appendChild(langBadge);
      
      header.addEventListener('click', () => {{
        showNodeDetails(node);
      }});
      
      wrapper.appendChild(header);
      
      if (node.children && node.children.length) {{
        const childrenContainer = document.createElement('div');
        childrenContainer.className = 'tree-node-children';
        node.children.forEach(child => renderTree(child, childrenContainer));
        wrapper.appendChild(childrenContainer);
        
        toggle.addEventListener('click', (e) => {{
          e.stopPropagation();
          const collapsed = childrenContainer.style.display === 'none';
          childrenContainer.style.display = collapsed ? 'block' : 'none';
          toggle.textContent = collapsed ? '▼' : '▶';
        }});
      }}
      
      container.appendChild(wrapper);
    }}

    // Display Node Details in panel
    function showNodeDetails(node) {{
      state.selectedNode = node;
      detailsPanel.classList.add('open');
      
      const isBookmarked = state.bookmarks.includes(node.id);
      
      detailsContent.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <strong>ID:</strong> <code style="font-family:var(--font-mono); font-size:0.75rem;">${{node.id}}</code>
          <button class="bookmark-btn ${{isBookmarked ? 'bookmarked' : ''}}" onclick="toggleBookmark('${{node.id}}')">
            ${{isBookmarked ? '★ Starred' : '☆ Star'}}
          </button>
        </div>
        <div><strong>Label:</strong> <span>${{node.label}}</span></div>
        <div><strong>Type:</strong> <span class="node-badge" style="background:var(--border-color);">${{node.node_type}}</span></div>
        ${{node.language ? `<div><strong>Language:</strong> <span>${{node.language}}</span></div>` : ''}}
        ${{node.file_path ? `<div><strong>File Path:</strong> <div style="font-family:var(--font-mono); font-size:0.75rem; word-break:break-all;">${{node.file_path}}</div></div>` : ''}}
        ${{node.class_name ? `<div><strong>Class:</strong> <span>${{node.class_name}}</span></div>` : ''}}
        ${{node.method_name ? `<div><strong>Method:</strong> <span>${{node.method_name}}</span></div>` : ''}}
        ${{node.framework ? `<div><strong>Framework:</strong> <span>${{node.framework}}</span></div>` : ''}}
        ${{node.line ? `<div><strong>Line Number:</strong> <span>${{node.line}}</span></div>` : ''}}
        ${{node.edge_relation ? `<div><strong>Called via:</strong> <span>${{node.edge_relation}} (${{node.call_type || 'sync'}})</span></div>` : ''}}
        ${{node.stop_reason ? `<div style="color:var(--accent-warning);"><strong>Stop Reason:</strong> <span>${{node.stop_reason}}</span></div>` : ''}}
        <div><strong>Traversal Depth:</strong> <span>${{node.depth}}</span></div>
        <div><strong>Execution Order:</strong> <span>${{node.execution_order}}</span></div>
      `;
    }}

    window.toggleBookmark = function(nodeId) {{
      const idx = state.bookmarks.indexOf(nodeId);
      if (idx > -1) {{
        state.bookmarks.splice(idx, 1);
      }} else {{
        state.bookmarks.push(nodeId);
      }}
      localStorage.setItem('journey_bookmarks', JSON.stringify(state.bookmarks));
      updateBookmarksUI();
      if (state.selectedNode && state.selectedNode.id === nodeId) {{
        showNodeDetails(state.selectedNode);
      }}
    }};

    function updateBookmarksUI() {{
      bookmarksList.innerHTML = '';
      if (!state.bookmarks.length) {{
        bookmarksList.innerHTML = '<p style="color: var(--text-muted); font-style: italic;">No bookmarks starred yet.</p>';
        return;
      }}
      
      const flat = getFlatNodes(state.currentJourney.root);
      state.bookmarks.forEach(id => {{
        const node = flat.find(n => n.id === id);
        if (node) {{
          const item = document.createElement('div');
          item.style.cssText = 'display:flex; justify-content:space-between; align-items:center; background:var(--bg-main); padding:6px 10px; border-radius:4px;';
          item.innerHTML = `
            <span style="font-family:var(--font-mono); font-size:0.75rem; text-overflow:ellipsis; overflow:hidden; white-space:nowrap; max-width:180px;">${{node.label}}</span>
            <button class="bookmark-btn bookmarked" onclick="toggleBookmark('${{id}}')">★</button>
          `;
          item.addEventListener('click', () => showNodeDetails(node));
          bookmarksList.appendChild(item);
        }}
      }});
    }}

    // Filter dropdown generation
    function initFilters() {{
      const flat = getFlatNodes(state.currentJourney.root);
      const langs = new Set();
      const fws = new Set();
      
      flat.forEach(n => {{
        if (n.language) langs.add(n.language);
        if (n.framework) fws.add(n.framework);
      }});
      
      langs.forEach(l => {{
        const opt = document.createElement('option');
        opt.value = l;
        opt.textContent = l;
        langFilter.appendChild(opt);
      }});

      fws.forEach(f => {{
        const opt = document.createElement('option');
        opt.value = f;
        opt.textContent = f;
        fwFilter.appendChild(opt);
      }});

      // Attach filter change listeners
      searchInput.addEventListener('input', applyFilters);
      depthSlider.addEventListener('input', (e) => {{
        depthVal.textContent = e.target.value;
        applyFilters();
      }});
      langFilter.addEventListener('change', applyFilters);
      fwFilter.addEventListener('change', applyFilters);
    }}

    function applyFilters() {{
      state.filters.search = searchInput.value.toLowerCase();
      state.filters.maxDepth = parseInt(depthSlider.value);
      state.filters.language = langFilter.value;
      state.filters.framework = fwFilter.value;

      // Re-render UI views according to filters
      renderAllViews();
    }}

    // Stats tab view
    function renderStats() {{
      const stats = state.currentJourney.statistics;
      statsGrid.innerHTML = `
        <div class="stats-card">
          <div class="stats-card-value">${{stats.node_count}}</div>
          <div class="stats-card-label">Total Nodes</div>
        </div>
        <div class="stats-card">
          <div class="stats-card-value">${{stats.maximum_depth}}</div>
          <div class="stats-card-label">Maximum Depth</div>
        </div>
        <div class="stats-card">
          <div class="stats-card-value">${{stats.average_depth.toFixed(1)}}</div>
          <div class="stats-card-label">Average Depth</div>
        </div>
        <div class="stats-card">
          <div class="stats-card-value">${{stats.edge_count}}</div>
          <div class="stats-card-label">Edges Count</div>
        </div>
        <div class="stats-card">
          <div class="stats-card-value">${{stats.cycle_count}}</div>
          <div class="stats-card-label">Cycles Detected</div>
        </div>
        <div class="stats-card">
          <div class="stats-card-value">${{stats.recursion_count}}</div>
          <div class="stats-card-label">Recursion Calls</div>
        </div>
      `;
    }}

    // Timeline tab view
    function renderTimeline() {{
      timelineContainer.innerHTML = '';
      const flat = getFlatNodes(state.currentJourney.root)
        .sort((a, b) => a.execution_order - b.execution_order);

      flat.forEach(node => {{
        if (node.depth > state.filters.maxDepth) return;
        if (state.filters.language !== 'all' && node.language !== state.filters.language) return;
        if (state.filters.framework !== 'all' && node.framework !== state.filters.framework) return;
        if (state.filters.search && !node.label.toLowerCase().includes(state.filters.search)) return;

        const item = document.createElement('div');
        item.className = 'timeline-item';
        item.innerHTML = `
          <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:var(--text-muted); margin-bottom:4px;">
            <span>Step #${{node.execution_order}}</span>
            <span>Depth ${{node.depth}}</span>
          </div>
          <div style="font-weight:600; font-family:var(--font-mono); font-size:0.875rem;">${{node.label}}</div>
          ${{node.file_path ? `<div style="font-size:0.75rem; color:var(--text-muted); word-break:break-all;">${{node.file_path}}</div>` : ''}}
        `;
        item.addEventListener('click', () => showNodeDetails(node));
        timelineContainer.appendChild(item);
      }});
    }}

    // Paths view tab
    function renderPaths() {{
      pathsContainer.innerHTML = '';
      const paths = state.currentJourney.execution_paths || [];
      if (!paths.length) {{
        pathsContainer.innerHTML = '<p style="color:var(--text-muted); font-style:italic;">No pre-computed execution paths available.</p>';
        return;
      }}

      paths.forEach((p, idx) => {{
        const card = document.createElement('div');
        card.className = 'path-card';
        
        let stepsHtml = p.labels.map(l => `<span style="background:var(--bg-main); padding:2px 6px; border-radius:4px;">${{l}}</span>`).join('<span class="path-arrow">→</span>');
        
        card.innerHTML = `
          <div class="path-card-title">Execution Path #${{idx+1}} (${{p.depth}} nodes)</div>
          <div class="path-flow-steps">${{stepsHtml}}</div>
        `;
        pathsContainer.appendChild(card);
      }});
    }}

    // Force-directed Canvas solver (no external dependencies)
    let simulation = null;
    function initGraphView() {{
      const canvas = document.getElementById('graph-canvas');
      const container = document.getElementById('graph-canvas-container');
      const ctx = canvas.getContext('2d');
      
      // Handle resizing
      canvas.width = container.clientWidth;
      canvas.height = container.clientHeight;
      
      const flat = getFlatNodes(state.currentJourney.root);
      const links = state.currentJourney.edges || [];
      
      // Node positioning and simulation properties
      const nodes = flat.map(n => ({{
        id: n.id,
        label: n.label,
        node_type: n.node_type,
        x: canvas.width / 2 + (Math.random() - 0.5) * 150,
        y: canvas.height / 2 + (Math.random() - 0.5) * 150,
        vx: 0,
        vy: 0,
        radius: 20
      }}));

      const nodeMap = new Map(nodes.map(n => [n.id, n]));

      // Physics solver loop
      let animFrame = null;
      let scale = 1.0;
      let offsetX = 0;
      let offsetY = 0;
      let isDragging = false;
      let dragStart = {{ x: 0, y: 0 }};
      let draggedNode = null;

      function solvePhysics() {{
        const k = 120; // rest distance
        const rep = 800; // repulsion coefficient
        const attr = 0.05; // attraction coefficient
        
        // 1. Repulsion between all node pairs
        for (let i = 0; i < nodes.length; i++) {{
          const n1 = nodes[i];
          for (let j = i + 1; j < nodes.length; j++) {{
            const n2 = nodes[j];
            const dx = n2.x - n1.x;
            const dy = n2.y - n1.y;
            const dist = Math.sqrt(dx*dx + dy*dy) || 1;
            const fx = (rep / (dist * dist)) * (dx / dist);
            const fy = (rep / (dist * dist)) * (dy / dist);
            n1.vx -= fx;
            n1.vy -= fy;
            n2.vx += fx;
            n2.vy += fy;
          }}
        }}

        // 2. Attraction along links
        links.forEach(l => {{
          const s = nodeMap.get(l.source_id);
          const t = nodeMap.get(l.target_id);
          if (s && t) {{
            const dx = t.x - s.x;
            const dy = t.y - s.y;
            const dist = Math.sqrt(dx*dx + dy*dy) || 1;
            const force = attr * (dist - k);
            const fx = force * (dx / dist);
            const fy = force * (dy / dist);
            s.vx += fx;
            s.vy += fy;
            t.vx -= fx;
            t.vy -= fy;
          }}
        }});

        // 3. Gravity pulling toward center + update positions
        const cx = canvas.width / 2;
        const cy = canvas.height / 2;
        nodes.forEach(n => {{
          n.vx += (cx - n.x) * 0.005;
          n.vy += (cy - n.y) * 0.005;
          
          if (n === draggedNode) return;
          
          n.x += n.vx;
          n.y += n.vy;
          
          // Apply friction
          n.vx *= 0.85;
          n.vy *= 0.85;
        }});
      }}

      function draw() {{
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.save();
        ctx.translate(offsetX, offsetY);
        ctx.scale(scale, scale);

        // Draw edges
        ctx.strokeStyle = '#64748b';
        ctx.lineWidth = 1.5;
        links.forEach(l => {{
          const s = nodeMap.get(l.source_id);
          const t = nodeMap.get(l.target_id);
          if (s && t) {{
            ctx.beginPath();
            ctx.moveTo(s.x, s.y);
            ctx.lineTo(t.x, t.y);
            ctx.stroke();
            
            // Draw simple arrow in the middle
            const mx = (s.x + t.x) / 2;
            const my = (s.y + t.y) / 2;
            const angle = Math.atan2(t.y - s.y, t.x - s.x);
            ctx.fillStyle = '#64748b';
            ctx.beginPath();
            ctx.arc(mx, my, 4, 0, 2*Math.PI);
            ctx.fill();
          }}
        }});

        // Draw nodes
        nodes.forEach(n => {{
          ctx.fillStyle = '#3b82f6';
          ctx.beginPath();
          ctx.arc(n.x, n.y, n.radius, 0, 2 * Math.PI);
          ctx.fill();
          
          ctx.fillStyle = 'white';
          ctx.strokeStyle = '#1e3a8a';
          ctx.lineWidth = 2;
          ctx.stroke();
          
          // Node Label
          ctx.fillStyle = '#f8fafc';
          ctx.font = '9px JetBrains Mono';
          ctx.textAlign = 'center';
          ctx.fillText(n.label.slice(0, 10), n.x, n.y + 3);
        }});

        ctx.restore();
      }}

      function tick() {{
        solvePhysics();
        draw();
        animFrame = requestAnimationFrame(tick);
      }}

      // Interaction listeners
      canvas.addEventListener('mousedown', (e) => {{
        const rect = canvas.getBoundingClientRect();
        const mx = (e.clientX - rect.left - offsetX) / scale;
        const my = (e.clientY - rect.top - offsetY) / scale;
        
        // Check if node is clicked
        draggedNode = nodes.find(n => {{
          const dx = n.x - mx;
          const dy = n.y - my;
          return Math.sqrt(dx*dx + dy*dy) < n.radius;
        }});
        
        if (draggedNode) {{
          const matchingOrig = flat.find(n => n.id === draggedNode.id);
          showNodeDetails(matchingOrig);
        }} else {{
          isDragging = true;
          dragStart = {{ x: e.clientX - offsetX, y: e.clientY - offsetY }};
        }}
      }});

      canvas.addEventListener('mousemove', (e) => {{
        if (draggedNode) {{
          const rect = canvas.getBoundingClientRect();
          draggedNode.x = (e.clientX - rect.left - offsetX) / scale;
          draggedNode.y = (e.clientY - rect.top - offsetY) / scale;
        }} else if (isDragging) {{
          offsetX = e.clientX - dragStart.x;
          offsetY = e.clientY - dragStart.y;
        }}
      }});

      canvas.addEventListener('mouseup', () => {{
        draggedNode = null;
        isDragging = false;
      }});

      // Zoom listener
      canvas.addEventListener('wheel', (e) => {{
        e.preventDefault();
        const zoomFactor = 1.1;
        if (e.deltaY < 0) {{
          scale *= zoomFactor;
        }} else {{
          scale /= zoomFactor;
        }}
      }});

      document.getElementById('zoom-in').onclick = () => scale *= 1.2;
      document.getElementById('zoom-out').onclick = () => scale /= 1.2;
      document.getElementById('zoom-fit').onclick = () => {{
        scale = 1.0;
        offsetX = 0;
        offsetY = 0;
        nodes.forEach((n, i) => {{
          n.x = canvas.width / 2 + (Math.random() - 0.5) * 150;
          n.y = canvas.height / 2 + (Math.random() - 0.5) * 150;
        }});
      }};

      tick();
    }}

    function renderAllViews() {{
      treeContainer.innerHTML = '';
      renderTree(state.currentJourney.root, treeContainer);
      renderTimeline();
      renderPaths();
      renderStats();
      updateBookmarksUI();
    }}

    // Initialization
    initFilters();
    renderAllViews();

  </script>
</body>
</html>
"""


def write_journey_html(ir: JourneyIR, path: Path) -> None:
    """Write journey HTML view output file."""
    data = journey_ir_to_dict(ir)
    data_json = json.dumps(data, ensure_ascii=False)
    html_content = html_template(data_json, is_forest=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_content, encoding="utf-8")


def write_forest_html(forest: JourneyForest, path: Path) -> None:
    """Write journey forest HTML view output file."""
    data = journey_forest_to_dict(forest)
    data_json = json.dumps(data, ensure_ascii=False)
    html_content = html_template(data_json, is_forest=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_content, encoding="utf-8")
