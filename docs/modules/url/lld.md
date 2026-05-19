# URL and Web Low-Level Design

## Class and module responsibilities

| Symbol | Responsibility |
|--------|----------------|
| `convert_url` | Public entry / orchestration |
| `run_crawl` | Public entry / orchestration |
| `convert_one_page_artifact` | Public entry / orchestration |

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
| `src\md_generator\url\__init__.py` | Implementation |
| `src\md_generator\url\api\__init__.py` | Implementation |
| `src\md_generator\url\api\convert_runner.py` | Implementation |
| `src\md_generator\url\api\jobs.py` | Implementation |
| `src\md_generator\url\api\main.py` | Implementation |
| `src\md_generator\url\api\mcp_server.py` | Implementation |
| `src\md_generator\url\api\mcp_setup.py` | Implementation |
| `src\md_generator\url\api\query_options.py` | Implementation |
| `src\md_generator\url\api\settings.py` | Implementation |
| `src\md_generator\url\assets.py` | Implementation |
| `src\md_generator\url\convert_impl.py` | Implementation |
| `src\md_generator\url\converter.py` | Implementation |
| ... | (20 Python files total) |


