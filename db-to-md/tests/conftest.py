from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def db_api_client() -> TestClient:
    """Single FastAPI lifespan per test session (MCP session manager is single-use)."""
    root = Path(tempfile.mkdtemp())
    os.environ["DB_TO_MD_JOB_SQLITE_PATH"] = str(root / "jobs.sqlite")
    os.environ["DB_TO_MD_JOB_WORKSPACE_ROOT"] = str(root / "ws")
    from md_generator.db.api.main import app

    with TestClient(app, raise_server_exceptions=True) as client:
        yield client
