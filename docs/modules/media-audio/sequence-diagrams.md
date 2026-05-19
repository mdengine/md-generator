# Audio Sequence Diagrams

## Synchronous HTTP conversion

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant Core as media-audio_core
    Client->>API: POST /convert/sync
    API->>Core: convert
    Core-->>API: artifact bytes/path
    API-->>Client: 200 + body or FileResponse
```

## CLI invocation

```mermaid
sequenceDiagram
    participant User
    participant CLI as md-audio
    participant Core as media-audio_core
    User->>CLI: argv
    CLI->>Core: main()
    Core-->>CLI: exit code
    CLI-->>User: stdout/stderr
```
