from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from md_generator.sap.core.extractor import extract_to_markdown
from md_generator.sap.core.run_config import SapRunConfig

logger = logging.getLogger(__name__)


@dataclass
class SapJobRecord:
    job_id: str
    status: str
    progress: int
    current: str
    workspace: str
    zip_path: str | None
    error: str | None
    created_at: float
    updated_at: float

    def to_api_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "progress": self.progress,
            "current": self.current,
            "workspace": self.workspace,
            "zip_path": self.zip_path,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def _zip_dir(src_dir: Path, dest_zip: Path) -> None:
    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(src_dir.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(src_dir).as_posix())


def _default_sqlite_path() -> Path:
    return Path.home() / ".mdengine" / "sap_jobs.db"


class SapJobManager:
    def __init__(
        self,
        *,
        sqlite_path: str | Path | None = None,
        workspace_root: Path | None = None,
        in_memory: bool = False,
    ) -> None:
        self._lock = threading.Lock()
        self._root = Path(workspace_root) if workspace_root else None
        if in_memory:
            self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        else:
            path = Path(sqlite_path or _default_sqlite_path())
            path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sap_jobs (
                job_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                current TEXT NOT NULL DEFAULT '',
                workspace TEXT NOT NULL,
                zip_path TEXT,
                error TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                config_json TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def enqueue(self, cfg: SapRunConfig) -> str:
        job_id = str(uuid.uuid4())
        ws = (self._root or Path.cwd() / "sap_jobs") / job_id
        ws.mkdir(parents=True, exist_ok=True)
        now = time.time()
        cfg_out = cfg.with_output(ws / "output")
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO sap_jobs (job_id, status, progress, current, workspace, zip_path, error, created_at, updated_at, config_json)
                VALUES (?, 'PENDING', 0, '', ?, NULL, NULL, ?, ?, ?)
                """,
                (job_id, str(ws), now, now, json.dumps({"input_paths": [str(p) for p in cfg.input_paths]})),
            )
            self._conn.commit()
        t = threading.Thread(target=self._run_job, args=(job_id, cfg_out, ws), daemon=True)
        t.start()
        return job_id

    def _run_job(self, job_id: str, cfg: SapRunConfig, ws: Path) -> None:
        try:
            self._update(job_id, "RUNNING", 0, "start")

            def on_progress(pct: int, current: str) -> None:
                self._update(job_id, "RUNNING", pct, current)

            extract_to_markdown(cfg)
            zip_path = ws / "output.zip"
            _zip_dir(cfg.output_path, zip_path)
            self._update(job_id, "COMPLETED", 100, "done", zip_path=str(zip_path))
        except Exception as e:
            logger.exception("SAP job %s failed", job_id)
            self._update(job_id, "FAILED", 0, "error", error=str(e))

    def _update(
        self,
        job_id: str,
        status: str,
        progress: int,
        current: str,
        *,
        zip_path: str | None = None,
        error: str | None = None,
    ) -> None:
        now = time.time()
        with self._lock:
            if zip_path:
                self._conn.execute(
                    "UPDATE sap_jobs SET status=?, progress=?, current=?, zip_path=?, updated_at=? WHERE job_id=?",
                    (status, progress, current, zip_path, now, job_id),
                )
            elif error:
                self._conn.execute(
                    "UPDATE sap_jobs SET status=?, progress=?, current=?, error=?, updated_at=? WHERE job_id=?",
                    (status, progress, current, error, now, job_id),
                )
            else:
                self._conn.execute(
                    "UPDATE sap_jobs SET status=?, progress=?, current=?, updated_at=? WHERE job_id=?",
                    (status, progress, current, now, job_id),
                )
            self._conn.commit()

    def get(self, job_id: str) -> SapJobRecord | None:
        row = self._conn.execute("SELECT * FROM sap_jobs WHERE job_id=?", (job_id,)).fetchone()
        if not row:
            return None
        return SapJobRecord(
            job_id=row["job_id"],
            status=row["status"],
            progress=row["progress"],
            current=row["current"],
            workspace=row["workspace"],
            zip_path=row["zip_path"],
            error=row["error"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
