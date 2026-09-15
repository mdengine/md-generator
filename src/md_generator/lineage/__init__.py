"""Lineage, deterministic identity, and manifest package for md_generator."""

from .ids import (
    normalize_source_uri,
    generate_canonical_json,
    compute_content_hash,
    generate_document_id,
    generate_revision_id,
    canonicalize_semantic_key,
    generate_chunk_id,
)
from .manifest import (
    DeltaState,
    DeltaReason,
    ManifestEntry,
    VersionedManifest,
    evaluate_delta,
)

__all__ = [
    "normalize_source_uri",
    "generate_canonical_json",
    "compute_content_hash",
    "generate_document_id",
    "generate_revision_id",
    "canonicalize_semantic_key",
    "generate_chunk_id",
    "DeltaState",
    "DeltaReason",
    "ManifestEntry",
    "VersionedManifest",
    "evaluate_delta",
]
