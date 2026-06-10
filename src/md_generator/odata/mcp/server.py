from __future__ import annotations

import base64
import tempfile
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from md_generator.odata.core.extractor import extract_to_markdown
from md_generator.odata.core.run_config import OdataRunConfig
from md_generator.odata.core.zip_export import build_markdown_zip_bytes
from md_generator.odata.parser.registry import parse_document


def build_mcp_stack(*, mount_under_fastapi: bool = False) -> tuple[FastMCP, object]:
    path = "/" if mount_under_fastapi else "/mcp"
    mcp = FastMCP(
        "odata-to-md",
        instructions="Convert OData CSDL metadata (V1-V4, XML/JSON) to Markdown catalogs.",
        streamable_http_path=path,
    )

    @mcp.tool()
    def odata_validate_metadata(metadata_text: str) -> str:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as tmp:
            tmp.write(metadata_text)
            p = Path(tmp.name)
        try:
            doc = parse_document(p, metadata_text)
            return f"ok: OData {doc.odata_version.value} service={doc.service_name} entities={len(doc.entity_types)}"
        except Exception as e:
            return f"error: {e}"
        finally:
            p.unlink(missing_ok=True)

    @mcp.tool()
    def odata_generate_readme_markdown(metadata_text: str) -> str:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as tmp:
            tmp.write(metadata_text)
            p = Path(tmp.name)
        try:
            with tempfile.TemporaryDirectory() as td:
                out = Path(td) / "out"
                cfg = OdataRunConfig(file=p, output_path=out).normalized()
                extract_to_markdown(cfg)
                index = out / "odata" / "index.md"
                return index.read_text(encoding="utf-8") if index.is_file() else ""
        finally:
            p.unlink(missing_ok=True)

    @mcp.tool()
    def odata_run_sync_zip_base64(metadata_text: str) -> str:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as tmp:
            tmp.write(metadata_text)
            p = Path(tmp.name)
        try:
            cfg = OdataRunConfig(file=p, output_path=Path(".")).normalized()
            data = build_markdown_zip_bytes(cfg)
            return base64.b64encode(data).decode("ascii")
        finally:
            p.unlink(missing_ok=True)

    sub = mcp.streamable_http_app()
    return mcp, sub
