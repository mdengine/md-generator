from __future__ import annotations

from dataclasses import dataclass

from md_generator.codeflow.enterprise_ir.base import BaseEntity


@dataclass
class StorageEntity(BaseEntity):
    storage_type: str  # local, s3, azure_blob, gcs
    path_or_bucket: str
    access_permissions: str | None = None  # read, write, read-write
