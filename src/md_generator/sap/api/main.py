from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import ValidationError

from md_generator.sap.api.schemas import SapToMdRunBody
from md_generator.sap.api.settings import SapApiSettings, cors_list, sqlite_path_resolved
from md_generator.sap.api.zip_export import build_sap_markdown_zip_bytes
from md_generator.sap.core.job_manager import SapJobManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = SapApiSettings()
    ws = Path(settings.job_workspace_root) if settings.job_workspace_root else None
    jobs = SapJobManager(sqlite_path=sqlite_path_resolved(settings), workspace_root=ws)
    app.state.settings = settings
    app.state.jobs = jobs
    yield
    jobs.close()


app = FastAPI(title="sap-to-md", lifespan=lifespan)
_bootstrap = SapApiSettings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_list(_bootstrap),
    allow_credentials="*" not in cors_list(_bootstrap),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/sap-to-md/run")
async def sap_run_sync(body: SapToMdRunBody) -> Response:
    try:
        cfg = body.to_run_config()
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()) from e
    if not cfg.input_paths:
        raise HTTPException(status_code=400, detail="input.paths required")
    data = build_sap_markdown_zip_bytes(cfg)
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="sap-md.zip"'},
    )


@app.post("/sap-to-md/job")
async def sap_enqueue(body: SapToMdRunBody, request: Request) -> dict[str, str]:
    cfg = body.to_run_config()
    if not cfg.input_paths:
        raise HTTPException(status_code=400, detail="input.paths required")
    jobs: SapJobManager = request.app.state.jobs
    job_id = jobs.enqueue(cfg)
    return {"job_id": job_id}


@app.get("/sap-to-md/job/{job_id}")
async def sap_job_status(job_id: str, request: Request) -> dict:
    jobs: SapJobManager = request.app.state.jobs
    rec = jobs.get(job_id)
    if not rec:
        raise HTTPException(status_code=404, detail="job not found")
    return rec.to_api_dict()


@app.get("/sap-to-md/job/{job_id}/download")
async def sap_job_download(job_id: str, request: Request) -> FileResponse:
    jobs: SapJobManager = request.app.state.jobs
    rec = jobs.get(job_id)
    if not rec or rec.status != "COMPLETED" or not rec.zip_path:
        raise HTTPException(status_code=404, detail="zip not ready")
    return FileResponse(rec.zip_path, filename="sap-md.zip", media_type="application/zip")
