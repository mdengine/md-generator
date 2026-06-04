from __future__ import annotations

import io
import zipfile
from pathlib import Path

from md_generator.odata.core.extractor import extract_to_markdown
from md_generator.odata.core.run_config import OdataRunConfig


def build_markdown_zip_bytes(cfg: OdataRunConfig) -> bytes:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "out"
        cfg_run = cfg.with_output(root)
        extract_to_markdown(cfg_run)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in sorted(root.rglob("*")):
                if p.is_file():
                    zf.write(p, p.relative_to(root).as_posix())
        return buf.getvalue()
