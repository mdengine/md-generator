from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from md_generator.sap.parser.odata.fetch import fetch_metadata, infer_service_root

FIXTURES = Path(__file__).parent / "fixtures" / "odata"


def test_infer_service_root():
    root = infer_service_root("https://example.com/sap/opu/odata/sap/API_PRODUCT/$metadata")
    assert root == "https://example.com/sap/opu/odata/sap/API_PRODUCT"


def test_fetch_metadata_caches(tmp_path: Path):
    xml_bytes = (FIXTURES / "metadata.xml").read_bytes()
    mock_resp = MagicMock()
    mock_resp.content = xml_bytes
    mock_resp.raise_for_status = MagicMock()
    with patch("httpx.get", return_value=mock_resp) as mock_get:
        p1 = fetch_metadata("https://example.com/$metadata", tmp_path, timeout=5)
        p2 = fetch_metadata("https://example.com/$metadata", tmp_path, timeout=5)
    assert p1 == p2
    assert p1.is_file()
    mock_get.assert_called_once()
