from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

from md_generator.sap.core.extractor import extract_to_markdown
from md_generator.sap.core.run_config import SapRunConfig


def build_sap_markdown_zip_bytes(cfg: SapRunConfig) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "out"
        cfg = cfg.with_output(root)
        extract_to_markdown(cfg)
        buf = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        buf.close()
        zpath = Path(buf.name)
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in sorted(root.rglob("*")):
                if p.is_file():
                    zf.write(p, p.relative_to(root).as_posix())
        data = zpath.read_bytes()
        zpath.unlink(missing_ok=True)
        return data
