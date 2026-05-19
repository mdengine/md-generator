# Video Low-Level Design

## Class and module responsibilities

| Symbol | Responsibility |
|--------|----------------|
| `VideoToMarkdownService` | Public entry / orchestration |
| `video_probe_from_ffprobe` | Public entry / orchestration |

## Call sequence (CLI)

```mermaid
sequenceDiagram
    participant Main as main
    participant Parser as argparse
    participant Core as converter
    Main->>Parser: parse argv
    Parser->>Core: options + paths
    Core-->>Main: result
```

## File map

| Path | Role |
|------|------|
| `src\md_generator\media\video\__init__.py` | Implementation |
| `src\md_generator\media\video\api\__init__.py` | Implementation |
| `src\md_generator\media\video\api\main.py` | Implementation |
| `src\md_generator\media\video\api\mcp_server.py` | Implementation |
| `src\md_generator\media\video\api\mcp_setup.py` | Implementation |
| `src\md_generator\media\video\api\run.py` | Implementation |
| `src\md_generator\media\video\api\settings.py` | Implementation |
| `src\md_generator\media\video\converter.py` | Implementation |
| `src\md_generator\media\video\formatter.py` | Implementation |
| `src\md_generator\media\video\service.py` | Implementation |
| ... | (10 Python files total) |


