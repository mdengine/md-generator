from __future__ import annotations

import hashlib
from enum import Enum
from pathlib import Path


class ArtifactType(str, Enum):
    ABAP = "abap"
    CDS = "cds"
    DDIC = "ddic"
    ODATA = "odata"
    HANA_CALCULATION_VIEW = "hana.calculation_view"
    BW_ADSO = "bw.adso"
    DATASPHERE_VIEW = "datasphere.view"
    UNKNOWN = "unknown"


def file_checksum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
