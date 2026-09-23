"""Vector domain models, composite keying, numeric validation, and atomic manifest store."""

import os
import json
import math
import tempfile
import urllib.parse
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set

from md_generator.semantic.model.schema import SourceLocation
from md_generator.vector.exceptions import (
    VectorValueError,
    VectorDimensionMismatchError,
    CollectionConfigurationError,
)

EMBEDDING_ID_ALGORITHM_VERSION = "1"


def validate_vector(vector: List[float], expected_dimension: Optional[int] = None) -> None:
    """Validates numeric vector finiteness, magnitude, and dimension bounds without float overflow."""
    if not isinstance(vector, list) or len(vector) == 0:
        raise VectorValueError("Vector must be a non-empty list of float values.")

    for val in vector:
        if isinstance(val, bool) or not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
            raise VectorValueError(f"Vector contains invalid non-numeric or non-finite float value: {val}")

    try:
        norm = math.hypot(*vector)
    except (OverflowError, TypeError):
        raise VectorValueError("Vector magnitude computation overflowed or failed.")

    if norm == 0.0:
        raise VectorValueError("Vector magnitude cannot be zero.")

    if expected_dimension is not None and len(vector) != expected_dimension:
        raise VectorDimensionMismatchError(
            f"Vector dimension {len(vector)} does not match collection dimension {expected_dimension}."
        )


def manifest_document_key(tenant_id: str, document_id: str) -> str:
    """Generates a delimiter-safe, injective composite key for document-to-chunks manifest lookup."""
    encoded_tenant = urllib.parse.quote(tenant_id or "", safe="")
    encoded_doc = urllib.parse.quote(document_id or "", safe="")
    return f"tenant:{encoded_tenant}:doc:{encoded_doc}"


def manifest_record_key(tenant_id: str, collection_name: str, embedding_id: str) -> str:
    """Generates a delimiter-safe, injective composite key for vector sync record manifest lookup."""
    encoded_tenant = urllib.parse.quote(tenant_id or "", safe="")
    encoded_coll = urllib.parse.quote(collection_name or "", safe="")
    encoded_emb = urllib.parse.quote(embedding_id or "", safe="")
    return f"tenant:{encoded_tenant}:collection:{encoded_coll}:embedding:{encoded_emb}"


@dataclass
class EmbeddingRecord:
    embedding_id: str
    chunk_id: str
    document_id: str
    vector: List[float]
    dimension: int
    provider_name: str
    model_name: str
    model_version: str
    sanitized_content: str
    semantic_key: str
    tenant_id: str
    entity_type: Optional[str] = None
    parent_chunk_id: Optional[str] = None
    source_location: Optional[SourceLocation] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_vector(self.vector, self.dimension)


@dataclass
class VectorQueryResult:
    embedding_id: str
    chunk_id: str
    score: float
    sanitized_content: str
    semantic_key: str
    tenant_id: str
    entity_type: Optional[str] = None
    parent_chunk_id: Optional[str] = None
    source_location: Optional[SourceLocation] = None
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollectionConfig:
    collection_name: str = "enterprise_knowledge"
    dimension: Optional[int] = None
    distance_metric: str = "cosine"

    def __post_init__(self) -> None:
        if not self.collection_name or not isinstance(self.collection_name, str):
            raise CollectionConfigurationError("collection_name must be a non-empty string.")
        if self.dimension is not None and (not isinstance(self.dimension, int) or self.dimension <= 0):
            raise CollectionConfigurationError("dimension must be a positive integer or None.")
        if self.distance_metric not in {"cosine", "dot", "euclidean"}:
            raise CollectionConfigurationError("distance_metric must be one of 'cosine', 'dot', or 'euclidean'.")


@dataclass
class VectorSyncRecord:
    tenant_id: str
    document_id: str
    revision_id: str
    document_semantic_processing_fingerprint: str
    chunk_id: str
    chunk_semantic_processing_fingerprint: str
    provider_name: str
    model_name: str
    model_version: str
    embedding_processing_fingerprint: str
    embedding_id: str
    collection_name: str
    created_timestamp: float


@dataclass
class VectorSyncManifest:
    version: str = "1.0"
    records: Dict[str, VectorSyncRecord] = field(default_factory=dict)
    document_to_chunks: Dict[str, List[str]] = field(default_factory=dict)


class VectorSyncManifestStore:
    """Single-writer atomic persistence manager for VectorSyncManifest using standard library."""

    @staticmethod
    def load(filepath: str) -> VectorSyncManifest:
        if not os.path.exists(filepath):
            return VectorSyncManifest()
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return VectorSyncManifestStore._from_dict(data)

    @staticmethod
    def save_atomic(manifest: VectorSyncManifest, filepath: str) -> None:
        dirname = os.path.dirname(filepath)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        data = VectorSyncManifestStore._to_dict(manifest)
        temp_fd, temp_path = tempfile.mkstemp(dir=dirname, prefix=".manifest_tmp_")
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, sort_keys=True)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, filepath)
        except Exception:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            raise

    @staticmethod
    def _to_dict(manifest: VectorSyncManifest) -> Dict[str, Any]:
        records_dict = {}
        for k, v in manifest.records.items():
            records_dict[k] = asdict(v)
        return {
            "version": manifest.version,
            "records": records_dict,
            "document_to_chunks": manifest.document_to_chunks,
        }

    @staticmethod
    def _from_dict(data: Dict[str, Any]) -> VectorSyncManifest:
        version = data.get("version", "1.0")
        records_raw = data.get("records", {})
        records = {}
        for k, v in records_raw.items():
            records[k] = VectorSyncRecord(
                tenant_id=v["tenant_id"],
                document_id=v["document_id"],
                revision_id=v["revision_id"],
                document_semantic_processing_fingerprint=v["document_semantic_processing_fingerprint"],
                chunk_id=v["chunk_id"],
                chunk_semantic_processing_fingerprint=v["chunk_semantic_processing_fingerprint"],
                provider_name=v["provider_name"],
                model_name=v["model_name"],
                model_version=v["model_version"],
                embedding_processing_fingerprint=v["embedding_processing_fingerprint"],
                embedding_id=v["embedding_id"],
                collection_name=v["collection_name"],
                created_timestamp=v["created_timestamp"],
            )
        doc_to_chunks = data.get("document_to_chunks", {})
        return VectorSyncManifest(
            version=version,
            records=records,
            document_to_chunks=doc_to_chunks,
        )
