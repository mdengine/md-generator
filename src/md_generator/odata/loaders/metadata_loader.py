from __future__ import annotations

import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from md_generator.odata.fetch import fetch_metadata
from md_generator.odata.loaders.discovery import discover_metadata_files, is_odata_metadata


@dataclass
class LoadedMetadata:
    paths: list[Path] = field(default_factory=list)
    url_map: dict[Path, str] = field(default_factory=dict)
    cleanup_dirs: list[Path] = field(default_factory=list)


def _extract_zip(zip_path: Path) -> Path:
    td = Path(tempfile.mkdtemp(prefix="odata-to-md-zip-"))
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(td)
    return td


def load_odata_source(
    *,
    file: Path | None = None,
    folder: Path | None = None,
    zip_path: Path | None = None,
    urls: list[str] | None = None,
    cache_dir: Path | None = None,
    fetch_timeout_sec: int = 30,
) -> LoadedMetadata:
    url_list = [u for u in (urls or []) if str(u).strip()]
    file_sources = sum(1 for x in (file, folder, zip_path) if x is not None)
    if file_sources > 1:
        raise ValueError("Specify at most one of: file, folder, zip (urls may be combined with folder/file)")
    if file_sources == 0 and not url_list:
        raise ValueError("Specify at least one of: file, folder, zip, url(s)")

    loaded = LoadedMetadata()
    cache = cache_dir or Path(tempfile.mkdtemp(prefix="odata-fetch-"))

    if file is not None:
        p = file.expanduser().resolve()
        if not p.is_file():
            raise FileNotFoundError(p)
        if not is_odata_metadata(p):
            raise ValueError(f"Not recognized as OData metadata: {p}")
        loaded.paths.append(p)

    if folder is not None:
        root = folder.expanduser().resolve()
        if not root.is_dir():
            raise FileNotFoundError(root)
        loaded.paths.extend(discover_metadata_files([root]))

    if zip_path is not None:
        zp = zip_path.expanduser().resolve()
        if not zp.is_file():
            raise FileNotFoundError(zp)
        td = _extract_zip(zp)
        loaded.cleanup_dirs.append(td)
        loaded.paths.extend(discover_metadata_files([td]))

    for url in url_list:
        p = fetch_metadata(url, cache, timeout=fetch_timeout_sec)
        loaded.paths.append(p)
        loaded.url_map[p] = url

    loaded.paths = list(dict.fromkeys(loaded.paths))
    if not loaded.paths:
        raise FileNotFoundError("No OData metadata files found")
    return loaded
