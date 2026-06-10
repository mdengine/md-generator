from __future__ import annotations

import re


def safe_filename(stable_id: str, suffix: str = "") -> str:
    """Filesystem-safe name derived from stable_id (Windows forbids ':')."""
    base = re.sub(r"[^\w.\-]+", "_", stable_id.replace("::", "__"))
    return f"{base}{suffix}"
