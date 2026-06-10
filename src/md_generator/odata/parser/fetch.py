from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse


def infer_service_root(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if path.endswith("$metadata"):
        path = path[: -len("$metadata")].rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{path}" if parsed.netloc else path


def fetch_metadata(url: str, cache_dir: Path, *, timeout: int = 30) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w.-]", "_", url)[:120]
    dest = cache_dir / f"{safe}_metadata.xml"
    if dest.is_file():
        return dest
    try:
        import httpx

        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        content = resp.content
        if b"$EntityType" in content or b"@odata.context" in content:
            dest = cache_dir / f"{safe}_metadata.json"
        dest.write_bytes(content)
        return dest
    except ImportError as e:
        raise RuntimeError("httpx required for OData URL fetch: pip install mdengine[sap]") from e
