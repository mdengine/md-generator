# Graph Metadata Configuration

Configuration surfaces:

1. **CLI flags** — `md-graph --help`
2. **Environment variables** — see `parameters.md`
3. **Run config dataclasses** — `src/md_generator/graph/**/run_config.py`
4. **YAML presets** — `src\md_generator\graph\config\default.yaml`

## YAML keys (extracted defaults)

| Config file | Key | Default / sample |
| --- | --- | --- |
| src\md_generator\graph\config\default.yaml | graph.source | 'networkx' |
| src\md_generator\graph\config\default.yaml | graph.uri | 'bolt://localhost:7687' |
| src\md_generator\graph\config\default.yaml | graph.database | 'neo4j' |
| src\md_generator\graph\config\default.yaml | graph.user | 'neo4j' |
| src\md_generator\graph\config\default.yaml | graph.password | 'password' |
| src\md_generator\graph\config\default.yaml | graph.graph_file | null |
| src\md_generator\graph\config\default.yaml | graph.neo4j_id_mode | 'element_id' |
| src\md_generator\graph\config\default.yaml | graph.neo4j_page_size | 500 |
| src\md_generator\graph\config\default.yaml | graph.connection_timeout_s | 30.0 |
| src\md_generator\graph\config\default.yaml | graph.depth | 2 |
| src\md_generator\graph\config\default.yaml | graph.start_node | null |
| src\md_generator\graph\config\default.yaml | graph.max_nodes | 10000 |
| src\md_generator\graph\config\default.yaml | graph.max_edges | 50000 |
| src\md_generator\graph\config\default.yaml | output.path | './docs' |
| src\md_generator\graph\config\default.yaml | output.split_files | True |
| src\md_generator\graph\config\default.yaml | output.combine_markdown | True |
| src\md_generator\graph\config\default.yaml | execution.mode | 'async' |
| src\md_generator\graph\config\default.yaml | execution.workers | 4 |
| src\md_generator\graph\config\default.yaml | viz.enabled | False |
| src\md_generator\graph\config\default.yaml | viz.mermaid | True |
| src\md_generator\graph\config\default.yaml | viz.formats | 'png', 'svg' |


## Example

```bash
md-graph --help
```

For HTTP services, configure upload limits and CORS via module `settings.py` environment variables.
