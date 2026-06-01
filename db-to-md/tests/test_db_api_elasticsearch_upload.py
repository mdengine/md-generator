from __future__ import annotations

import io
import json
import zipfile
from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient


def _minimal_es_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "mappings/test.json",
            json.dumps({"properties": {"x": {"type": "keyword"}}}),
        )
        zf.writestr("settings/test.json", json.dumps({"index": {}}))
    return buf.getvalue()


def test_run_elasticsearch_upload_sync_returns_zip(db_api_client: TestClient) -> None:
    zip_bytes = _minimal_es_zip()
    with patch(
        "md_generator.db.api.main.build_markdown_zip_bytes",
        return_value=b"PK\x03\x04fake",
    ):
        resp = db_api_client.post(
            "/db-to-md/run/elasticsearch",
            files={"file": ("bundle.zip", zip_bytes, "application/zip")},
        )
    assert resp.status_code == 200
    assert "application/zip" in resp.headers.get("content-type", "")


def test_run_elasticsearch_upload_rejects_non_zip(db_api_client: TestClient) -> None:
    resp = db_api_client.post(
        "/db-to-md/run/elasticsearch",
        files={"file": ("bad.txt", b"not a zip", "text/plain")},
    )
    assert resp.status_code == 400
