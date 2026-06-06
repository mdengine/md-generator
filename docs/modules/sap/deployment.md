# SAP Intelligence Deployment

## CLI-only

Install extras in container image; invoke `md-sap` as Job/Cron.

## Docker API

If `sap-to-md/Dockerfile.api` exists, build and run uvicorn with `--root-path /sap-to-md` behind gateway (`deploy/docker-compose.yml`).

## Resources

| Tier | Guidance |
|------|----------|
| CPU | Scale with OCR/Whisper/browser workloads |
| Memory | Large PDFs/archives need higher limits |
| Disk | Temp job workspaces — mount ephemeral volume |

Configure proxy body size and timeouts (see `deploy/nginx/default.conf`).
