from __future__ import annotations

"""Deterministic ID Generation & Canonical Identity Module.

Phase 0B-2 Implementation: Standard library only deterministic SHA-256 ID generation,
cross-platform URI normalization, and Phase 0A canonical JSON serialization rules.
"""

from typing import Any, Dict
import hashlib
import json
import os
import re

from md_generator.semantic.model.schema import InvalidSchemaError, _validate_hex_id


def normalize_source_uri(uri: str) -> str:
    """Normalize source URI cross-platform while preserving path casing semantics."""
    if not isinstance(uri, str):
        raise InvalidSchemaError("source_uri must be a string.")
    clean = uri.strip().replace("\\", "/")
    # Standardize drive letters (e.g. C:/path -> c:/path)
    if len(clean) > 1 and clean[1] == ":":
        clean = clean[0].lower() + clean[1:]
    return clean.strip()


def generate_canonical_json(data: Dict[str, Any]) -> str:
    """Generate Phase 0A deterministic canonical JSON serialization."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of text content."""
    if not isinstance(content, str):
        raise InvalidSchemaError("content must be a string.")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def generate_document_id(source_uri: str, source_type: str, repository: str = "") -> str:
    """Generate perpetual logical document ID based on repository, source_type, and normalized URI."""
    if not source_uri or not isinstance(source_uri, str):
        raise InvalidSchemaError("source_uri must be a non-empty string.")
    if not source_type or not isinstance(source_type, str):
        raise InvalidSchemaError("source_type must be a non-empty string.")

    norm_uri = normalize_source_uri(source_uri)
    data = {
        "normalized_uri": norm_uri,
        "repository": repository.strip(),
        "source_type": source_type.strip().lower(),
    }
    canonical_json = generate_canonical_json(data)
    doc_id = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    _validate_hex_id(doc_id, "document_id", exact_length=True)
    return doc_id


def generate_revision_id(
    document_id: str,
    content_hash: str,
    commit: str = "",
    policy_hash: str = ""
) -> str:
    """Generate content/commit version revision ID."""
    _validate_hex_id(document_id, "document_id", exact_length=True)
    if not content_hash or not isinstance(content_hash, str):
        raise InvalidSchemaError("content_hash must be a non-empty string.")

    data = {
        "commit": commit.strip(),
        "content_hash": content_hash.strip(),
        "document_id": document_id,
        "policy_hash": policy_hash.strip(),
    }
    canonical_json = generate_canonical_json(data)
    rev_id = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    _validate_hex_id(rev_id, "revision_id", exact_length=True)
    return rev_id


def canonicalize_semantic_key(domain_type: str, raw_key: str) -> str:
    """Format domain-specific semantic key (e.g. class:com.company.PaymentService)."""
    if not domain_type or not isinstance(domain_type, str):
        raise InvalidSchemaError("domain_type must be a non-empty string.")
    if not raw_key or not isinstance(raw_key, str):
        raise InvalidSchemaError("raw_key must be a non-empty string.")
    return f"{domain_type.strip().lower()}:{raw_key.strip()}"


def generate_chunk_id(document_id: str, semantic_key: str, chunk_content_hash: str) -> str:
    """Generate semantic chunk ID based on document_id, semantic_key, and content_hash."""
    _validate_hex_id(document_id, "document_id", exact_length=True)
    if not semantic_key or not isinstance(semantic_key, str):
        raise InvalidSchemaError("semantic_key must be a non-empty string.")
    if not chunk_content_hash or not isinstance(chunk_content_hash, str):
        raise InvalidSchemaError("chunk_content_hash must be a non-empty string.")

    data = {
        "content_hash": chunk_content_hash.strip(),
        "document_id": document_id,
        "semantic_key": semantic_key.strip(),
    }
    canonical_json = generate_canonical_json(data)
    chunk_id = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    _validate_hex_id(chunk_id, "chunk_id", exact_length=True)
    return chunk_id
