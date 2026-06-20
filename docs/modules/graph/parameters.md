# Graph Metadata Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `--config` | Path | optional | None | — | Path to YAML config |
| `--source` | str | optional | None | ('networkx', 'neo4j') | — |
| `--uri` | str | optional | None | — | — |
| `--user` | str | optional | None | — | — |
| `--password` | str | optional | None | — | — |
| `--database` | str | optional | None | — | Neo4j database name (e.g. neo4j); passed to driver session(database=...) |
| `--graph-file` | Path | optional | None | — | — |
| `--depth` | int | optional | None | — | — |
| `--start-node` | str | optional | None | — | — |
| `--max-nodes` | int | optional | None | — | — |
| `--max-edges` | int | optional | None | — | — |
| `--output` | Path | optional | None | — | — |
| `--neo4j-id-mode` | str | optional | None | ('element_id', 'internal_id') | — |
| `--async` | flag | optional | false | — | Enqueue background job (prints job_id; uses SQLite job store) |
| `--markdown-layout` | str | optional | None | ('combined', 'individual') | combined (default): nodes.md, relationship.md, graph_summary with embedded sections; individual: nodes/ and relationships/ per entity |
| `--individual` | flag | optional | false | — | Shortcut for --markdown-layout individual |
| `--viz` | flag | optional | false | — | Write output/graph/graph.dot and render PNG/SVG/PDF via Graphviz dot (if installed) |
| `--viz-formats` | str | optional | None | — | Comma-separated formats for --viz (default png,svg). Example: png,svg,pdf |
| `--no-mermaid` | flag | optional | false | — | Disable Mermaid diagram (graph/graph.mmd and README fenced block) |


## API routes (HTTP parameters)

| Method | Path | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| GET | /health | HTTP | — | — | FastAPI route |
| POST | /graph-to-md/run | HTTP | — | — | FastAPI route |
| POST | /graph-to-md/job | HTTP | — | — | FastAPI route |
| GET | /graph-to-md/job/{job_id} | HTTP | — | — | FastAPI route |
| GET | /graph-to-md/job/{job_id}/download | HTTP | — | — | FastAPI route |
| GET | /graph-to-md/job/{job_id}/events | HTTP | — | — | FastAPI route |
| GET | /graph-to-md/job/{job_id}/stream | HTTP | — | — | FastAPI route |


## Environment variables

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| GRAPH_TO_MD_PORT | string/int | optional | varies | — | HTTP API listen port |


## Config files

| File | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| src\md_generator\graph\config\default.yaml | YAML | optional | — | — | Packaged or preset config |


## YAML config keys (from packaged defaults)

| File | Key | Default / sample | Required | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| src\md_generator\graph\config\default.yaml | graph.source | 'networkx' | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | graph.uri | 'bolt://localhost:7687' | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | graph.database | 'neo4j' | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | graph.user | 'neo4j' | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | graph.password | 'password' | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | graph.graph_file | null | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | graph.neo4j_id_mode | 'element_id' | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | graph.neo4j_page_size | 500 | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | graph.connection_timeout_s | 30.0 | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | graph.depth | 2 | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | graph.start_node | null | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | graph.max_nodes | 10000 | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | graph.max_edges | 50000 | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | output.path | './docs' | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | output.split_files | True | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | output.combine_markdown | True | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | execution.mode | 'async' | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | execution.workers | 4 | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | viz.enabled | False | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | viz.mermaid | True | optional | — | From packaged YAML |
| src\md_generator\graph\config\default.yaml | viz.formats | 'png', 'svg' | optional | — | From packaged YAML |


## Run config dataclass fields

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| VizConfig | enabled | bool | varies | False | Run config dataclass field |
| VizConfig | mermaid | bool | varies | True | Run config dataclass field |
| VizConfig | formats | tuple[str, ...] | varies | ('png', 'svg') | Run config dataclass field |
| GraphRunConfig | source | str | varies | 'networkx' | Run config dataclass field |
| GraphRunConfig | uri | str | varies | '' | Run config dataclass field |
| GraphRunConfig | user | str | varies | '' | Run config dataclass field |
| GraphRunConfig | password | str | varies | '' | Run config dataclass field |
| GraphRunConfig | graph_file | Path \| None | varies | None | Run config dataclass field |
| GraphRunConfig | neo4j_id_mode | str | varies | 'element_id' | Run config dataclass field |
| GraphRunConfig | neo4j_database | str \| None | varies | None | Run config dataclass field |
| GraphRunConfig | neo4j_page_size | int | varies | 500 | Run config dataclass field |
| GraphRunConfig | connection_timeout_s | float | varies | 30.0 | Run config dataclass field |
| GraphRunConfig | depth | int | varies | 0 | Run config dataclass field |
| GraphRunConfig | start_node | str \| None | varies | None | Run config dataclass field |
| GraphRunConfig | max_nodes | int | varies | 10000 | Run config dataclass field |
| GraphRunConfig | max_edges | int | varies | 50000 | Run config dataclass field |
| GraphRunConfig | output_path | Path | varies | field(default_factory=lambda: Path('docs')) | Run config dataclass field |
| GraphRunConfig | split_files | bool | varies | True | Run config dataclass field |
| GraphRunConfig | combine_markdown | bool | varies | True | Run config dataclass field |
| GraphRunConfig | workers | int | varies | 4 | Run config dataclass field |
| GraphRunConfig | viz | VizConfig | varies | field(default_factory=VizConfig) | Run config dataclass field |


## Options / dataclass fields (sample)

| Class | Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- | --- |
| GraphSection | source | str | varies | — | Field on options/config class |
| GraphSection | uri | str | varies | — | Field on options/config class |
| GraphSection | user | str | varies | — | Field on options/config class |
| GraphSection | password | str | varies | — | Field on options/config class |
| GraphSection | database | str \| None | varies | — | Field on options/config class |
| GraphSection | graph_file | str \| None | varies | — | Field on options/config class |
| GraphSection | neo4j_id_mode | str | varies | — | Field on options/config class |
| GraphSection | neo4j_page_size | int | varies | — | Field on options/config class |
| GraphSection | connection_timeout_s | float | varies | — | Field on options/config class |
| GraphSection | depth | int | varies | — | Field on options/config class |
| GraphSection | start_node | str \| None | varies | — | Field on options/config class |
| GraphSection | max_nodes | int | varies | — | Field on options/config class |
| GraphSection | max_edges | int | varies | — | Field on options/config class |
| OutputSection | path | str | varies | — | Field on options/config class |
| OutputSection | split_files | bool | varies | — | Field on options/config class |
| OutputSection | combine_markdown | bool | varies | — | Field on options/config class |
| ExecutionSection | workers | int | varies | — | Field on options/config class |
| VizSection | enabled | bool | varies | — | Field on options/config class |
| VizSection | mermaid | bool | varies | — | Field on options/config class |
| VizSection | formats | list[str] | varies | — | Field on options/config class |
| VizConfig | enabled | bool | varies | — | Field on options/config class |
| VizConfig | mermaid | bool | varies | — | Field on options/config class |
| VizConfig | formats | tuple[str, ...] | varies | — | Field on options/config class |
| GraphRunConfig | source | str | varies | — | Field on options/config class |
| GraphRunConfig | uri | str | varies | — | Field on options/config class |
| GraphRunConfig | user | str | varies | — | Field on options/config class |
| GraphRunConfig | password | str | varies | — | Field on options/config class |
| GraphRunConfig | graph_file | Path \| None | varies | — | Field on options/config class |
| GraphRunConfig | neo4j_id_mode | str | varies | — | Field on options/config class |
| GraphRunConfig | neo4j_database | str \| None | varies | — | Field on options/config class |
| GraphRunConfig | neo4j_page_size | int | varies | — | Field on options/config class |
| GraphRunConfig | connection_timeout_s | float | varies | — | Field on options/config class |
| GraphRunConfig | depth | int | varies | — | Field on options/config class |
| GraphRunConfig | start_node | str \| None | varies | — | Field on options/config class |
| GraphRunConfig | max_nodes | int | varies | — | Field on options/config class |
| GraphRunConfig | max_edges | int | varies | — | Field on options/config class |
| GraphRunConfig | output_path | Path | varies | — | Field on options/config class |
| GraphRunConfig | split_files | bool | varies | — | Field on options/config class |
| GraphRunConfig | combine_markdown | bool | varies | — | Field on options/config class |
| GraphRunConfig | workers | int | varies | — | Field on options/config class |


## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `graph`.
