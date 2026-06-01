"""Load Elasticsearch metadata from a JSON directory or ZIP bundle."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Any


def read_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json_map(directory: Path) -> dict[str, Any]:
    """``{stem: parsed_json}`` for each ``*.json`` in ``directory``."""
    if not directory.is_dir():
        return {}
    out: dict[str, Any] = {}
    for p in sorted(directory.glob("*.json")):
        if p.is_file():
            out[p.stem] = read_json_file(p)
    return out


def extract_zip_bundle(zip_bytes: bytes, dest: Path) -> Path:
    """Extract ZIP to ``dest`` and return the bundle root directory."""
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        zf.extractall(dest)
    if (dest / "mappings").is_dir() or (dest / "settings").is_dir():
        return dest
    subs = [p for p in dest.iterdir() if p.is_dir()]
    if len(subs) == 1 and (
        (subs[0] / "mappings").is_dir()
        or (subs[0] / "settings").is_dir()
        or list(subs[0].glob("*.json"))
    ):
        return subs[0]
    return dest


def is_elasticsearch_bundle_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    if (path / "mappings").is_dir() or (path / "settings").is_dir():
        return True
    return bool(list(path.glob("*.json")))
