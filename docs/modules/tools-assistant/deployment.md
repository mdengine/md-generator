# AI Assistant Tools Deployment

## CLI-only

Install extras in container image; invoke `mdengine ai assist` as Job/Cron.

## Docker API

If `tool-assistant/Dockerfile.api` exists, build and run uvicorn with `--root-path /tool-assistant` behind gateway (`deploy/docker-compose.yml`).

## Resources

| Tier | Guidance |
|------|----------|
| CPU | Scale with OCR/Whisper/browser workloads |
| Memory | Large PDFs/archives need higher limits |
| Disk | Temp job workspaces — mount ephemeral volume |

Configure proxy body size and timeouts (see `deploy/nginx/default.conf`).
