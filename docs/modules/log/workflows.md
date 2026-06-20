# Log Analysis Workflows

## CLI workflow

1. Install `mdengine[log]`.
2. Run `md-log --help` to list flags.
3. Provide input (Log files, directories, OTLP sidecars, streaming sources (tail, Kafka, Redis, websocket, stdin)) and output path.
4. Inspect generated Markdown and sidecar assets.

## API workflow

1. Install `mdengine[log,api]`.
2. Start uvicorn on `md_generator.log` API module (see Deployment).
3. Call sync endpoint for small payloads or job endpoint for large conversions.
4. Poll job status and download artifact when complete.

## Processing pipeline

```mermaid
flowchart TD
    Start[Start] --> InputLoad[Load_input]
    InputLoad --> Validate[Validate_options]
    Validate --> Transform[Core_conversion]
    Transform --> Render[Render_Markdown]
    Render --> Package[Write_output_or_ZIP]
    Package --> End[Complete]
```

## Async job flow

Where job routes exist, background work uses in-process threads or domain job managers; results land in job workspace + download.

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Worker
    participant Storage
    Client->>API: POST job
    API->>Storage: create workspace
    API->>Worker: enqueue
    API-->>Client: job_id
    Worker->>Storage: write artifacts
    Client->>API: GET status/download
    API-->>Client: ZIP or Markdown
```

## Streaming and incremental processing

- **`md-log stream`** — tail, stdin, Kafka, Redis, or websocket sources (`streaming.*` in YAML).
- **`md-log presets`** — list parser presets (generic, springboot, logback, json, …).
- **`--resume`** — incremental checkpoint resume (`incremental.*` in YAML).
- **Knowledge graph** — enable `knowledge_graph.enabled` for service/event graph Markdown + Mermaid.

```mermaid
flowchart LR
    Source[files_or_stream] --> Ingest[ingestion]
    Ingest --> Parse[parser_presets]
    Parse --> Normalize[normalization]
    Normalize --> Enrich[enrichment_clustering]
    Enrich --> Graph[knowledge_graph_optional]
    Graph --> Emit[Markdown_JSONL_Parquet]
```

