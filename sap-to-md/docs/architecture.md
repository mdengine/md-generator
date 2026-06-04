# SAP module architecture

The `md_generator.sap` package mirrors **db** (metadata export), **codeflow** (dependency graphs), and **log** (semantic chunking).

## Pipeline v2 (canonical + graph)

When `pipeline.version >= 2` or `--pipeline-version 2`, the pipeline adds canonical JSON, ArtifactGraph merge, rule engine, and graph-based generators while preserving v1 Markdown output. See [canonical-model.md](canonical-model.md), [graph-model.md](graph-model.md), [hana-calculation-views.md](hana-calculation-views.md).

## Pipeline v1 (default)

1. Discover file-based SAP inputs
2. Parse via plugin registry (ABAP, CDS, DDIC, OData, BAPI, IDoc, transport)
3. Merge into `SapObject` IR
4. Build NetworkX knowledge graph
5. Run analyzers (relationships, governance, validation, authorization, lineage)
6. Emit split Markdown, optional chunks, graphs, manifest

## Entry points

- `extract_to_markdown(SapRunConfig)` — sync orchestrator
- `md-sap` / `mdengine sap-to-md` — CLI
- `md-sap-api` — FastAPI `/sap-to-md/*`
