# Codeflow CLI Reference

Command: **`md-codeflow`**  
Alternate: `codeflow / mdengine codeflow-to-md scan`

## Arguments

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


## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime conversion failure |
| 2 | Invalid usage or missing input |
