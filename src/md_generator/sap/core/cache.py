from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class ParseCache:
    """Incremental parse cache keyed by path, mtime, and size."""

    def __init__(self, cache_dir: Path | None, *, enabled: bool = True) -> None:
        self.enabled = enabled and cache_dir is not None
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir and self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key_path(self, path: Path) -> Path | None:
        if not self.cache_dir:
            return None
        h = hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]
        return self.cache_dir / f"{h}.json"

    def _fingerprint(self, path: Path) -> str:
        st = path.stat()
        return f"{st.st_mtime_ns}:{st.st_size}"

    def get(self, path: Path) -> dict[str, Any] | None:
        if not self.enabled or not path.is_file():
            return None
        cp = self._key_path(path)
        if not cp or not cp.is_file():
            return None
        try:
            data = json.loads(cp.read_text(encoding="utf-8"))
            if data.get("fingerprint") == self._fingerprint(path):
                return data.get("payload")
        except (json.JSONDecodeError, OSError):
            pass
        return None

    def put(self, path: Path, payload: dict[str, Any]) -> None:
        if not self.enabled:
            return
        cp = self._key_path(path)
        if not cp:
            return
        cp.write_text(
            json.dumps({"fingerprint": self._fingerprint(path), "payload": payload}, default=str),
            encoding="utf-8",
        )
