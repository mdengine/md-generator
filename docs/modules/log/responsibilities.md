# Log Analysis Responsibilities

## In scope

- pandas
- scikit-learn
- optional sentence-transformers
- Chroma export
- Kafka/Redis streaming
- archive bridge
- governance/MDAF hooks

- Expose `md-log` CLI for local and CI usage.
- Convert Log files, directories, OTLP sidecars, streaming sources (tail, Kafka, Redis, websocket, stdin) to Parsed events, summaries, incidents, knowledge graph, clustering, embedding exports, incremental checkpoints.
- Provide FastAPI + optional MCP integration.

## Platform extensions

- **Incremental** checkpoints and resume (`incremental.*`)
- **Knowledge graph** builder with optional Mermaid export
- **Streaming** coordinator (tail/Kafka/Redis/websocket)
- **Noise reduction**, correlation, topology, linking, governance/MDAF hooks
- **Archive bridge** for compressed log inputs (`ingestion.use_archive_bridge`)

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.
