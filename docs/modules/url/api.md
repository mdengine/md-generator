# URL and Web API

Service title: **url-to-md**  
Source: `src\md_generator\url\api\main.py`

## Endpoints

| Method | Path | Auth | Request | Response | Errors |
| --- | --- | --- | --- | --- | --- |
| POST | /convert/sync | See OpenAPI `/docs` | Upload/body per route | Job id or ZIP | Standard FastAPI errors |
| POST | /convert/jobs | See OpenAPI `/docs` | Upload/body per route | Job id or ZIP | Standard FastAPI errors |
| GET | /convert/jobs/{job_id} | See OpenAPI `/docs` | Upload/body per route | Job id or ZIP | Standard FastAPI errors |
| GET | /convert/jobs/{job_id}/download | See OpenAPI `/docs` | Upload/body per route | Job id or ZIP | Standard FastAPI errors |


## Sync vs async

- **Sync routes** return artifacts immediately (subject to size/time limits).
- **Job routes** return `job_id`; poll status/download endpoints until complete.
- **Event/stream routes** (domain modules) emit progress for long exports.

## Authentication

No built-in authentication middleware is enabled. Terminate TLS and authenticate at the reverse proxy or API gateway.

## Examples

```bash
curl -X POST http://localhost:8000/convert/sync \
  -F "file=@input.bin"
```

Open interactive docs at `/docs` when running uvicorn locally.

Many converter APIs mount MCP at `/mcp` when `mcp` extra is installed.
