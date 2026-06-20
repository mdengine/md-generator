# Codeflow Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `path` | str | required | None | — | Local directory, source file, .zip, or https/git remote URL (omit when using --clean-git-cache only) |
| `--output` | Path | optional | None | — | Output directory |
| `--entry` | str | optional | None | — | Comma-separated symbol ids (Class.method style) |
| `--lang` | str | optional | 'mixed' | — | mixed \| python \| java \| javascript \| typescript \| tsx \| cpp \| go \| php \| rust \| kotlin \| csharp \| swift \| ruby \| lua \| scala \| zig \| comma-separated (e.g. python,javascript). Aliases: js→javascript, ts→typescript. |
| `--formats` | str | optional | None | — | Comma-separated: md,html,mermaid,json |
| `--depth` | int | optional | 5 | — | — |
| `--include` | str | optional | None | — | Filter entry kinds: api,event,main,... |
| `--exclude` | str | optional | None | — | Reserved for path/symbol exclusions |
| `--async` | flag | optional | True | — | — |
| `--no-async` | str | optional | — | — | — |
| `--jobs` | flag | optional | False | — | No-op in CLI (reserved for API) |
| `--runtime` | flag | optional | False | — | Reserved: runtime tracing |
| `--business-rules` | str | optional | True | — | Emit business_rules.md, entry section, and (unless disabled) entry.combined.md (default: on) |
| `--business-rules-sql` | flag | optional | False | — | Scan workspace *.sql for CREATE TRIGGER lines |
| `--business-rules-combined` | str | optional | True | — | Write entry.combined.md (entry.md + business_rules.md) (default: on) |
| `--entry-fallback` | str | optional | 'roots' | ['none', 'roots', 'first_n'] | When no detected entries: none \| in-degree-0 roots \| first N symbols (default: roots) |
| `--entry-fallback-max` | int | optional | 20 | — | Max symbols when using roots or first_n fallback (default: 20) |
| `--emit-entry-per-method` | flag | optional | False | — | Emit one output slug per method/entry symbol (use --emit-entry-max to cap) |
| `--emit-entry-max` | int | optional | None | — | Cap for --emit-entry-per-method (default: 10000 when flag set and unset) |
| `--emit-entry-filter` | str | optional | None | — | Regex filter on symbol_id when using --emit-entry-per-method |
| `--entries-file` | Path | optional | None | — | File with one symbol_id per line (# comments allowed); resolved paths |
| `--no-scan-summary` | flag | optional | False | — | Skip writing scan-summary.md at output root |
| `--liferay-portlet-bases` | str | optional | None | — | Extra Liferay portlet superclass simple names (comma-separated); merged with built-in defaults |
| `--codeflow-config` | Path | optional | None | — | Path to codeflow.yaml (default: <project_root>/codeflow.yaml if present) |
| `--emit-flow-tree-json` | flag | optional | False | — | Write flow-tree.json (static DFS tree from the flow slice) beside each entry output |
| `-v` | flag | optional | False | — | Enable DEBUG logging for md_generator.codeflow |
| `--emit-graph-schema` | flag | optional | False | — | With json format, also write graph-schema.json (stable Node/Edge view with File/Class hierarchy) |
| `--intelligence-list-cap` | int | optional | 80 | — | Max items for Called by / Impact lists in Markdown (default: 80) |
| `--emit-cfg` | flag | optional | False | — | Build IR-based CFG per entry (cfg.json, cfg.mmd; append CFG Mermaid to flow.md when md is enabled) |
| `--cfg-max-nodes` | int | optional | 500 | — | Safety cap on CFG nodes when using --emit-cfg (default: 500) |
| `--cfg-inline-calls` | str | optional | False | — | When using --emit-cfg, inline callee CFGs at CALL nodes (default: off) |
| `--cfg-call-depth` | int | optional | 3 | — | Max CALL inlining depth when --cfg-inline-calls (default: 3) |
| `--cfg-max-paths` | int | optional | 100 | — | Max enumerated START→END paths when using --emit-cfg (default: 100) |
| `--cfg-path-max-depth` | int | optional | 1000 | — | Max DFS depth for path enumeration (default: 1000) |
| `--cfg-loop-visits` | int | optional | 2 | — | Max LOOP_HDR revisits per path before forcing exit edges (default: 2) |
| `--cfg-probability` | str | optional | False | — | Score enumerated CFG paths with default branch weights (and runtime trace if set) |
| `--cfg-mermaid-probabilities` | str | optional | False | — | Annotate cfg.mmd edges with static/runtime p= when using --emit-cfg |
| `--cfg-runtime-trace` | Path | optional | None | — | JSON file with counts {"u->v": n} to set CFG edge runtime_prob (optional) |
| `--cfg-loop-repeat-prob` | float | optional | 0.6 | — | Default probability for LOOP_HDR repeat edge (exit uses 1 minus this; default: 0.6) |
| `--cfg-ir-go` | str | optional | True | — | When using --emit-cfg, populate IR for Go from codeflow_go_dump (default: on) |
| `--cfg-ir-php` | str | optional | True | — | When using --emit-cfg, populate IR for PHP from codeflow_php_dump (default: on) |
| `--cfg-ir-cpp` | str | optional | True | — | When using --emit-cfg, populate IR for C/C++ via tree-sitter-cpp (default: on) |
| `--flow-include-event-edges` | str | optional | False | — | Include EVENT edges in flow slice and flow.mmd (pair with --include-events; default: off) |
| `--flow-include-reference-edges` | str | optional | False | — | Include REFERENCES edges in flow slice and flow.mmd (default: off) |
| `--event-impact` | str | optional | False | — | Add Event impact section (CALLS ∪ EVENT downstream) in entry.md (default: off) |
| `--enable-embeddings` | str | optional | False | — | Build local sentence embeddings (requires mdengine[codeflow-semantic]); cache under .codeflow_cache |
| `--embedding-model` | str | optional | 'all-MiniLM-L6-v2' | — | SentenceTransformers model id when --enable-embeddings (default: all-MiniLM-L6-v2) |
| `--embedding-max-nodes` | int | optional | 5000 | — | Max nodes to embed per scan (default: 5000) |
| `--embedding-k-clusters` | int | optional | 8 | — | K for KMeans semantic groups when cluster mode is semantic/hybrid (default: 8) |
| `--semantic-top-k` | int | optional | 10 | — | Top-K similar nodes per entry and for --semantic-search (default: 10) |
| `--semantic-search` | str | optional | None | — | When set with --enable-embeddings, write semantic-search-results.json (query embedding once) |
| `--emit-html-unified` | str | optional | False | — | Write index.unified.html per entry (Cytoscape + CFG Mermaid + semantic sidebar) |
| `--nl-query` | str | optional | None | — | Rule-based NL intent; writes nl-query-results.json (similar/impact/called by/event/…) |
| `--emit-runtime-insights` | str | optional | False | — | With --emit-cfg and --cfg-runtime-trace, write runtime-insights.json (hot paths + rare edges) |
| `--runtime-insight-frequency-threshold` | float | optional | 0.05 | — | Anomaly if edge count share of total trace mass is below this (default: 0.05) |
| `--runtime-insight-hot-paths-top` | int | optional | 5 | — | Number of hottest CFG paths to record (default: 5) |
| `--semantic-outlier-distance-threshold` | float | optional | 0.7 | — | With embeddings, flag nodes farther than 1-cosine from cluster centroid (default: 0.7) |
| `--graph-include-structural` | str | optional | False | — | Merge parser structural edges (IMPORTS / INHERITS / …; Java) into the graph (default: off) |
| `--enable-dependency-graph` | str | optional | False | — | Alias: enable structural IMPORTS/dependency edges (same merge as --graph-include-structural) |
| `--graph-include-contains-reachability` | str | optional | False | — | Include CONTAINS in dependency reachability (PR impact, Called by, Impact lists) |
| `--parser-mode` | str | optional | 'auto' | ('auto', 'treesitter', 'external') | auto=native parsers; treesitter=Tree-sitter for java/python/go/php/cpp (+ JS/TS when installed); external=clang only for C++ |
| `--ui-cfg-max-methods` | int | optional | 25 | — | Max methods in flow slice to embed CFG Mermaid in index.unified.html (default: 25) |
| `--ui` | str | optional | 'default' | ('default', 'unified') | unified: write index.unified.html (same as --emit-html-unified) |
| `--intelligence-transitive-callers` | str | optional | False | — | List transitive callers in Called By sections (default: direct only) |
| `--emit-system-graph-stats` | str | optional | False | — | Append graph inventory (counts, top out-degree) to system_overview.md |
| `--emit-graph-sqlite` | str | optional | False | — | Write graph.db (SQLite nodes/edges) alongside graph-full.json |
| `--graph-sqlite-mode` | str | optional | 'full' | ('full', 'incremental') | full replaces graph.db each scan; incremental upserts and appends scan metadata |
| `--graph-sqlite-prune-missing` | str | optional | False | — | incremental only: delete rows not seen in the latest scan |
| `--emit-graph-communities` | str | optional | False | — | When json format is on, write graph-communities.json (modularity; mode via --cluster-mode) |
| `--no-cluster-labels` | flag | optional | False | — | Disable rule-based community labels (use numeric ids only in Markdown) |
| `--include-references` | str | optional | False | — | Merge parser REFERENCES edges into the graph (Python/Java/TS heuristics) |
| `--include-events` | str | optional | False | — | Add Kafka topic nodes and EVENT edges (listeners + heuristic producers) for Java |
| `--cluster-mode` | str | optional | 'file_imports' | ('file_imports', 'structural', 'semantic', 'hybrid') | Clustering layer for graph-communities.json and entry.md cluster line |
| `--graph-query` | str | optional | None | — | Optional Cypher-like pattern (e.g. MATCH (a)-[CALLS]->(b)); writes query-results.json when json format is on |
| `--emit-llm-entry-sidecar` | str | optional | False | — | Write entry.llm.md beside each entry.md (pointers for LLM workflows) |
| `--git-branch` | str | optional | None | — | After clone/update, check out this branch (Git remote input only) |
| `--git-commit` | str | optional | None | — | After branch (or default), check out this commit SHA (Git remote input only) |
| `--git-auth-token` | str | optional | None | — | HTTPS token (injected per host; never printed). Prefer env-specific URLs in CI. |
| `--git-ssh-key` | Path | optional | None | — | Path to SSH private key for git@… remotes (sets GIT_SSH_COMMAND for clone/pull) |
| `--no-git-cache` | flag | optional | False | — | Delete cached clone for this URL and re-clone fresh |
| `--clean-git-cache` | flag | optional | False | — | Remove all cached Git clones under the codeflow cache dir, then exit (no scan) |
| `--multi-repo` | str | optional | None | — | Extra repository root to merge into one graph (repeatable); entries may be comma-separated |
| `--diff-base` | str | optional | None | — | With --diff-head, run git diff on project root and write pr-impact.json |
| `--diff-head` | str | optional | None | — | With --diff-base, run git diff on project root and write pr-impact.json |
| `--cross-repo-hints` | str | optional | None | — | JSON object: package prefix → repo label (used with --resolve-cross-repo after --multi-repo) |
| `--resolve-cross-repo` | flag | optional | False | — | Resolve external:: IMPORTS across merged repos using --cross-repo-hints |
| `--cross-repo-tsconfig` | str | optional | False | — | With --resolve-cross-repo, load tsconfig/jsconfig paths per repo for @… modules |
| `--cross-repo-maven-hints` | str | optional | False | — | With --resolve-cross-repo, add Maven pom.xml groupId→repo label hints |
| `--cache-ttl` | int | optional | 0 | — | If >0, skip git fetch/pull when clone metadata is younger than this many seconds (same branch/commit as last run; 0=off) |
| `--cache-clear` | str | optional | None | ('all', 'git', 'semantic', 'unified') | Clear caches before scan: git\|all wipes global clone cache first; scan also clears project .codeflow_cache for semantic\|unified\|all |
| `--no-cache-layer` | flag | optional | False | — | Disable git TTL skip and omit per-clone cache metadata writes |


## API routes (HTTP parameters)

| Method | Path | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| GET | /health | HTTP | — | — | FastAPI route |
| POST | /analyze | HTTP | — | — | FastAPI route |
| GET | /status/{job_id} | HTTP | — | — | FastAPI route |
| GET | /result/{job_id} | HTTP | — | — | FastAPI route |
| POST | /analyze/sync | HTTP | — | — | FastAPI route |
| GET | /analyze/job/{job_id}/events | HTTP | — | — | FastAPI route |


## Environment variables

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| CODEFLOW_CORS | string/int | optional | — | — | From `src\md_generator\codeflow\api\settings.py` |


## Config files

_No entries detected._


## YAML config keys (from packaged defaults)

_No entries detected._


## Run config dataclass fields

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| ScanConfig | project_root | Path | varies | — | Run config dataclass field |
| ScanConfig | output_path | Path | varies | — | Run config dataclass field |
| ScanConfig | paths_override | list[Path] \| None | varies | None | Run config dataclass field |
| ScanConfig | formats | tuple[str, ...] | varies | ('md', 'mermaid', 'json') | Run config dataclass field |
| ScanConfig | depth | int | varies | 5 | Run config dataclass field |
| ScanConfig | languages | str | varies | 'mixed' | Run config dataclass field |
| ScanConfig | entry | list[str] \| None | varies | None | Run config dataclass field |
| ScanConfig | include | str \| None | varies | None | Run config dataclass field |
| ScanConfig | exclude | str \| None | varies | None | Run config dataclass field |
| ScanConfig | include_internal | bool | varies | True | Run config dataclass field |
| ScanConfig | async_mode | bool | varies | True | Run config dataclass field |
| ScanConfig | jobs | bool | varies | False | Run config dataclass field |
| ScanConfig | runtime | bool | varies | False | Run config dataclass field |
| ScanConfig | business_rules | bool | varies | True | Run config dataclass field |
| ScanConfig | business_rules_sql | bool | varies | False | Run config dataclass field |
| ScanConfig | business_rules_combined | bool | varies | True | Run config dataclass field |
| ScanConfig | entry_fallback | Literal['none', 'roots', 'first_n'] | varies | 'roots' | Run config dataclass field |
| ScanConfig | entry_fallback_max | int | varies | 20 | Run config dataclass field |
| ScanConfig | emit_entry_per_method | bool | varies | False | Run config dataclass field |
| ScanConfig | emit_entry_max | int \| None | varies | None | Run config dataclass field |
| ScanConfig | emit_entry_filter | str \| None | varies | None | Run config dataclass field |
| ScanConfig | entries_file | Path \| None | varies | None | Run config dataclass field |
| ScanConfig | write_scan_summary | bool | varies | True | Run config dataclass field |
| ScanConfig | liferay_portlet_base_classes | tuple[str, ...] | varies | () | Run config dataclass field |
| ScanConfig | codeflow_config_path | Path \| None | varies | None | Run config dataclass field |
| ScanConfig | emit_flow_tree_json | bool | varies | False | Run config dataclass field |
| ScanConfig | verbose | bool | varies | False | Run config dataclass field |
| ScanConfig | emit_graph_schema | bool | varies | False | Run config dataclass field |
| ScanConfig | intelligence_list_cap | int | varies | 80 | Run config dataclass field |
| ScanConfig | emit_cfg | bool | varies | False | Run config dataclass field |
| ScanConfig | cfg_max_nodes | int | varies | 500 | Run config dataclass field |
| ScanConfig | cfg_inline_calls | bool | varies | False | Run config dataclass field |
| ScanConfig | cfg_call_depth | int | varies | 3 | Run config dataclass field |
| ScanConfig | cfg_max_paths | int | varies | 100 | Run config dataclass field |
| ScanConfig | cfg_path_max_depth | int | varies | 1000 | Run config dataclass field |
| ScanConfig | cfg_loop_visits | int | varies | 2 | Run config dataclass field |
| ScanConfig | cfg_probability | bool | varies | False | Run config dataclass field |
| ScanConfig | cfg_mermaid_probabilities | bool | varies | False | Run config dataclass field |
| ScanConfig | cfg_runtime_trace | Path \| None | varies | None | Run config dataclass field |
| ScanConfig | cfg_loop_repeat_prob | float | varies | 0.6 | Run config dataclass field |
| ScanConfig | graph_include_structural | bool | varies | False | Run config dataclass field |
| ScanConfig | include_references | bool | varies | False | Run config dataclass field |
| ScanConfig | include_events | bool | varies | False | Run config dataclass field |
| ScanConfig | cluster_mode | Literal['file_imports', 'structural', 'semantic', 'hybrid'] | varies | 'file_imports' | Run config dataclass field |
| ScanConfig | graph_query | str \| None | varies | None | Run config dataclass field |
| ScanConfig | intelligence_transitive_callers | bool | varies | False | Run config dataclass field |
| ScanConfig | emit_system_graph_stats | bool | varies | False | Run config dataclass field |
| ScanConfig | emit_graph_sqlite | bool | varies | False | Run config dataclass field |
| ScanConfig | graph_sqlite_mode | Literal['full', 'incremental'] | varies | 'full' | Run config dataclass field |
| ScanConfig | graph_sqlite_prune_missing | bool | varies | False | Run config dataclass field |
| ScanConfig | emit_graph_communities | bool | varies | False | Run config dataclass field |
| ScanConfig | emit_cluster_labels | bool | varies | True | Run config dataclass field |
| ScanConfig | emit_llm_entry_sidecar | bool | varies | False | Run config dataclass field |
| ScanConfig | cfg_ir_go | bool | varies | True | Run config dataclass field |
| ScanConfig | cfg_ir_php | bool | varies | True | Run config dataclass field |
| ScanConfig | cfg_ir_cpp | bool | varies | True | Run config dataclass field |
| ScanConfig | flow_include_event_edges | bool | varies | False | Run config dataclass field |
| ScanConfig | flow_include_reference_edges | bool | varies | False | Run config dataclass field |
| ScanConfig | event_impact | bool | varies | False | Run config dataclass field |
| ScanConfig | enable_embeddings | bool | varies | False | Run config dataclass field |
| ScanConfig | embedding_model | str | varies | 'all-MiniLM-L6-v2' | Run config dataclass field |
| ScanConfig | embedding_max_nodes | int | varies | 5000 | Run config dataclass field |
| ScanConfig | embedding_k_clusters | int | varies | 8 | Run config dataclass field |
| ScanConfig | semantic_top_k | int | varies | 10 | Run config dataclass field |
| ScanConfig | semantic_search | str \| None | varies | None | Run config dataclass field |
| ScanConfig | emit_html_unified | bool | varies | False | Run config dataclass field |
| ScanConfig | nl_query | str \| None | varies | None | Run config dataclass field |
| ScanConfig | emit_runtime_insights | bool | varies | False | Run config dataclass field |
| ScanConfig | runtime_insight_frequency_threshold | float | varies | 0.05 | Run config dataclass field |
| ScanConfig | runtime_insight_hot_paths_top | int | varies | 5 | Run config dataclass field |
| ScanConfig | semantic_outlier_distance_threshold | float | varies | 0.7 | Run config dataclass field |
| ScanConfig | multi_repo_roots | tuple[Path, ...] | varies | () | Run config dataclass field |
| ScanConfig | diff_base | str \| None | varies | None | Run config dataclass field |
| ScanConfig | diff_head | str \| None | varies | None | Run config dataclass field |
| ScanConfig | cross_repo_package_hints | dict[str, str] \| None | varies | None | Run config dataclass field |
| ScanConfig | resolve_cross_repo | bool | varies | False | Run config dataclass field |
| ScanConfig | cross_repo_tsconfig | bool | varies | False | Run config dataclass field |
| ScanConfig | cross_repo_maven_hints | bool | varies | False | Run config dataclass field |
| ScanConfig | cache_enabled | bool | varies | True | Run config dataclass field |
| ScanConfig | cache_ttl_seconds | int | varies | 0 | Run config dataclass field |


## Options / dataclass fields (sample)

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| AnalyzeOptions | formats | str \| None | varies | — | Field on options/config class |
| AnalyzeOptions | depth | int | varies | — | Field on options/config class |
| AnalyzeOptions | languages | str | varies | — | Field on options/config class |
| AnalyzeOptions | entry | str \| None | varies | — | Field on options/config class |
| AnalyzeOptions | include | str \| None | varies | — | Field on options/config class |
| AnalyzeOptions | exclude | str \| None | varies | — | Field on options/config class |
| AnalyzeOptions | business_rules | bool \| None | varies | — | Field on options/config class |
| AnalyzeOptions | business_rules_sql | bool \| None | varies | — | Field on options/config class |
| AnalyzeOptions | business_rules_combined | bool \| None | varies | — | Field on options/config class |
| AnalyzeOptions | entry_fallback | Literal['none', 'roots', 'first_n'] \| None | varies | — | Field on options/config class |
| AnalyzeOptions | entry_fallback_max | int \| None | varies | — | Field on options/config class |
| AnalyzeOptions | emit_entry_per_method | bool \| None | varies | — | Field on options/config class |
| AnalyzeOptions | emit_entry_max | int \| None | varies | — | Field on options/config class |
| AnalyzeOptions | emit_entry_filter | str \| None | varies | — | Field on options/config class |
| AnalyzeOptions | entries_file | str \| None | varies | — | Field on options/config class |
| AnalyzeOptions | write_scan_summary | bool \| None | varies | — | Field on options/config class |
| AnalyzeOptions | liferay_portlet_base_classes | str \| None | varies | — | Field on options/config class |
| AnalyzeOptions | codeflow_config_path | str \| None | varies | — | Field on options/config class |
| AnalyzeOptions | emit_flow_tree_json | bool \| None | varies | — | Field on options/config class |
| AnalyzeOptions | verbose | bool \| None | varies | — | Field on options/config class |
| AnalyzeOptions | emit_graph_schema | bool \| None | varies | — | Field on options/config class |
| AnalyzeOptions | intelligence_list_cap | int \| None | varies | — | Field on options/config class |
| AnalyzeOptions | emit_cfg | bool \| None | varies | — | Field on options/config class |
| AnalyzeOptions | cfg_max_nodes | int \| None | varies | — | Field on options/config class |
| AnalyzeOptions | cfg_inline_calls | bool \| None | varies | — | Field on options/config class |
| AnalyzeOptions | cfg_call_depth | int \| None | varies | — | Field on options/config class |
| AnalyzeOptions | cfg_max_paths | int \| None | varies | — | Field on options/config class |
| AnalyzeOptions | cfg_path_max_depth | int \| None | varies | — | Field on options/config class |
| AnalyzeOptions | cfg_loop_visits | int \| None | varies | — | Field on options/config class |
| AnalyzeOptions | cfg_probability | bool \| None | varies | — | Field on options/config class |
| AnalyzeOptions | cfg_mermaid_probabilities | bool \| None | varies | — | Field on options/config class |
| AnalyzeOptions | cfg_runtime_trace | str \| None | varies | — | Field on options/config class |
| AnalyzeOptions | cfg_loop_repeat_prob | float \| None | varies | — | Field on options/config class |
| AnalyzeOptions | graph_include_structural | bool \| None | varies | — | Field on options/config class |
| AnalyzeOptions | intelligence_transitive_callers | bool \| None | varies | — | Field on options/config class |
| AnalyzeOptions | emit_system_graph_stats | bool \| None | varies | — | Field on options/config class |
| AnalyzeOptions | emit_graph_sqlite | bool \| None | varies | — | Field on options/config class |
| AnalyzeOptions | graph_sqlite_mode | Literal['full', 'incremental'] \| None | varies | — | Field on options/config class |
| AnalyzeOptions | graph_sqlite_prune_missing | bool \| None | varies | — | Field on options/config class |
| AnalyzeOptions | emit_graph_communities | bool \| None | varies | — | Field on options/config class |


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `codeflow`.
