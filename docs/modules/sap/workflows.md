# SAP Intelligence Workflows

## CLI workflow

1. Install `mdengine[sap]`.
2. Run `md-sap --help` to list flags.
3. Provide input (ABAP, CDS/DDL, DDIC (ADT XML, abapGit `.tabl.xml`), HANA CV exports, BW, Datasphere, OData $metadata, BAPI, IDoc, transport files) and output path.
4. Inspect generated Markdown and sidecar assets.

## API workflow

1. Install `mdengine[sap,api]`.
2. Start uvicorn on `md_generator.sap` API module (see Deployment).
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

## SAP pipeline (v1 vs v2)

- **Pipeline v1** — legacy entity builder path.
- **Pipeline v2** — canonical JSON + artifact graph + registered generators (`--pipeline-version 2` or `pipeline.version: 2` in YAML).
- Enable **semantic narrative** (deterministic, no LLM) with `pipeline.semantic_narrative: true`.

```mermaid
flowchart TD
    Inputs[SAP_source_files] --> Discovery[Parser_registry]
    Discovery --> Canonical[CanonicalArtifact_JSON]
    Canonical --> Graph[Artifact_graph_store]
    Graph --> Generators[Generator_registry]
    Generators --> Markdown[Cross_linked_Markdown]
    Generators --> Sidecars[lineage_impact_mermaid]
    Markdown --> Chunks[Optional_semantic_chunks]
```

## Feature flags (`--include` / `--exclude`)

Supported values: `authorization`, `chunks`, `entities`, `functional`, `governance`, `graphs`, `json_output`, `lineage`, `odata_catalog`, `relationships`, `technical`, `validations`.

