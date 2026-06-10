from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("fastapi")

FIXTURES = Path(__file__).parent / "fixtures" / "odata"


def test_api_generate_zip():
    from md_generator.odata.api.main import app

    client = TestClient(app)
    xml = (FIXTURES / "metadata.xml").read_bytes()
    resp = client.post(
        "/odata-to-md/generate",
        files={"file": ("metadata.xml", xml, "application/xml")},
    )
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("application/zip")
    assert len(resp.content) > 100
