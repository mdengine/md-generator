# OpenTelemetry Traces Workflows

## CLI workflow

1. Install `mdengine[log-otel-proto]`.
2. Run `md-otel --help` to list flags.
3. Provide input (OTLP JSON or protobuf trace exports) and output path.
4. Inspect generated Markdown and sidecar assets.

## API workflow

1. Install `mdengine[log-otel-proto,api]`.
2. Start uvicorn on `md_generator.otel` API module (see Deployment).
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

Where job routes exist, background work uses in-process threads or domain job managers; results land in direct response.

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
