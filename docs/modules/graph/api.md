# Graph Metadata API

Service title: **graph-to-md**  
Source: `src\md_generator\graph\api\main.py`

## Endpoints

| Method | Path | Auth | Request | Response | Errors |
| --- | --- | --- | --- | --- | --- |
| GET | /health | See OpenAPI `/docs` | Upload/body per route | Job id or ZIP | Standard FastAPI errors |
| POST | /graph-to-md/run | See OpenAPI `/docs` | Upload/body per route | Job id or ZIP | Standard FastAPI errors |
| POST | /graph-to-md/job | See OpenAPI `/docs` | Upload/body per route | Job id or ZIP | Standard FastAPI errors |
| GET | /graph-to-md/job/{job_id} | See OpenAPI `/docs` | Upload/body per route | Job id or ZIP | Standard FastAPI errors |
| GET | /graph-to-md/job/{job_id}/download | See OpenAPI `/docs` | Upload/body per route | Job id or ZIP | Standard FastAPI errors |
| GET | /graph-to-md/job/{job_id}/events | See OpenAPI `/docs` | Upload/body per route | Job id or ZIP | Standard FastAPI errors |
| GET | /graph-to-md/job/{job_id}/stream | See OpenAPI `/docs` | Upload/body per route | Job id or ZIP | Standard FastAPI errors |


## Sync vs async

- **Sync routes** return artifacts immediately (subject to size/time limits).
- **Job routes** return `job_id`; poll status/download endpoints until complete.
- **Event/stream routes** (domain modules) emit progress for long exports.

## Authentication

No built-in authentication middleware is enabled. Terminate TLS and authenticate at the reverse proxy or API gateway.

## Examples

```bash
curl -X POST http://localhost:8000/health \
  -F "file=@input.bin"
```

Open interactive docs at `/docs` when running uvicorn locally.

Many converter APIs mount MCP at `/mcp` when `mcp` extra is installed.
