# OpenAPI Deployment

## CLI-only

Install extras in container image; invoke `md-openapi` as Job/Cron.

## Docker API

If `openapi-to-md/Dockerfile.api` exists, build and run uvicorn with `--root-path /openapi-to-md` behind gateway (`deploy/docker-compose.yml`).

## Resources

| Tier | Guidance |
|------|----------|
| CPU | Scale with OCR/Whisper/browser workloads |
| Memory | Large PDFs/archives need higher limits |
| Disk | Temp job workspaces — mount ephemeral volume |

Configure proxy body size and timeouts (see `deploy/nginx/default.conf`).
