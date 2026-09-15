from __future__ import annotations

"""Versioned Manifest & 5-State Delta Engine.

Phase 0B-3 Implementation: Standard library only manifest tracking,
5-state lifecycle evaluation, fine-grained delta reasons, and moved file detection.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import json

from md_generator.semantic.model.schema import InvalidSchemaError, _check_no_unknown_fields


class DeltaState(str, Enum):
    NEW = "NEW"
    MODIFIED = "MODIFIED"
    UNCHANGED = "UNCHANGED"
    DELETED = "DELETED"
    FAILED = "FAILED"


class DeltaReason(str, Enum):
    CREATED = "CREATED"
    CONTENT_CHANGED = "CONTENT_CHANGED"
    CONFIG_CHANGED = "CONFIG_CHANGED"
    MOVED = "MOVED"
    RENAMED = "RENAMED"
    REMOVED = "REMOVED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    PARSE_FAILED = "PARSE_FAILED"


@dataclass
class ManifestEntry:
    document_id: str
    revision_id: str
    source_uri: str
    content_hash: str
    last_processed_timestamp: float = 0.0
    chunk_ids: List[str] = field(default_factory=list)
    state: DeltaState = DeltaState.UNCHANGED
    reason: Optional[DeltaReason] = None
    error_details: Optional[Dict[str, Any]] = None  # Supports retry & error tracking

    def __post_init__(self) -> None:
        if isinstance(self.state, str):
            self.state = DeltaState(self.state)
        if isinstance(self.reason, str):
            self.reason = DeltaReason(self.reason)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["state"] = self.state.value
        if self.reason:
            d["reason"] = self.reason.value
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ManifestEntry:
        if not isinstance(data, dict):
            raise InvalidSchemaError("Input to from_dict must be a dictionary.")
        allowed = set(cls.__dataclass_fields__.keys())
        _check_no_unknown_fields(data, allowed, "ManifestEntry")
        try:
            return cls(**data)
        except (TypeError, ValueError) as e:
            raise InvalidSchemaError(f"Failed to instantiate ManifestEntry: {e}") from e


@dataclass
class VersionedManifest:
    manifest_schema_version: str = "1.0"
    pipeline_version: str = "1.0"
    semantic_schema_version: str = "1.0"
    chunker_version: str = "1.0"
    security_policy_version: str = "1.0"
    embedding_provider: str = ""
    embedding_model: str = ""
    embedding_dimension: int = 0
    distance_metric: str = "cosine"
    timestamp: float = 0.0
    entries: Dict[str, ManifestEntry] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_schema_version": self.manifest_schema_version,
            "pipeline_version": self.pipeline_version,
            "semantic_schema_version": self.semantic_schema_version,
            "chunker_version": self.chunker_version,
            "security_policy_version": self.security_policy_version,
            "embedding_provider": self.embedding_provider,
            "embedding_model": self.embedding_model,
            "embedding_dimension": self.embedding_dimension,
            "distance_metric": self.distance_metric,
            "timestamp": self.timestamp,
            "entries": {k: v.to_dict() for k, v in self.entries.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> VersionedManifest:
        if not isinstance(data, dict):
            raise InvalidSchemaError("Input to from_dict must be a dictionary.")
        allowed = set(cls.__dataclass_fields__.keys())
        _check_no_unknown_fields(data, allowed, "VersionedManifest")
        try:
            entries_data = data.get("entries", {})
            entries = {k: ManifestEntry.from_dict(v) for k, v in entries_data.items()}
            data_copy = dict(data)
            data_copy["entries"] = entries
            return cls(**data_copy)
        except (TypeError, ValueError) as e:
            raise InvalidSchemaError(f"Failed to instantiate VersionedManifest: {e}") from e

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> VersionedManifest:
        try:
            return cls.from_dict(json.loads(json_str))
        except json.JSONDecodeError as e:
            raise InvalidSchemaError(f"Invalid JSON format for VersionedManifest: {e}") from e


def evaluate_delta(
    previous_manifest: Optional[VersionedManifest],
    current_files: Dict[str, Dict[str, Any]],
    current_config_hash: str = ""
) -> Dict[str, ManifestEntry]:
    """Evaluate 5-state delta lifecycle across current files vs previous manifest.

    current_files maps source_uri -> {"document_id": str, "content_hash": str, "revision_id": str}
    """
    results: Dict[str, ManifestEntry] = {}
    prev_entries = previous_manifest.entries if previous_manifest else {}

    # Map content_hash -> list of old_uris to detect MOVED files
    hash_to_old_uris: Dict[str, List[str]] = {}
    for uri, entry in prev_entries.items():
        hash_to_old_uris.setdefault(entry.content_hash, []).append(uri)

    processed_prev_uris: Set[str] = set()

    for uri, info in current_files.items():
        doc_id = info["document_id"]
        rev_id = info["revision_id"]
        content_hash = info["content_hash"]

        if uri in prev_entries:
            processed_prev_uris.add(uri)
            prev_entry = prev_entries[uri]
            if prev_entry.content_hash == content_hash:
                results[uri] = ManifestEntry(
                    document_id=doc_id,
                    revision_id=rev_id,
                    source_uri=uri,
                    content_hash=content_hash,
                    chunk_ids=prev_entry.chunk_ids,
                    state=DeltaState.UNCHANGED,
                    reason=None,
                )
            else:
                results[uri] = ManifestEntry(
                    document_id=doc_id,
                    revision_id=rev_id,
                    source_uri=uri,
                    content_hash=content_hash,
                    state=DeltaState.MODIFIED,
                    reason=DeltaReason.CONTENT_CHANGED,
                )
        else:
            # Check if content_hash existed at another uri (MOVED / RENAMED)
            old_uris = hash_to_old_uris.get(content_hash, [])
            unprocessed_old = [u for u in old_uris if u not in current_files and u not in processed_prev_uris]
            if unprocessed_old:
                old_uri = unprocessed_old[0]
                processed_prev_uris.add(old_uri)
                prev_entry = prev_entries[old_uri]
                results[uri] = ManifestEntry(
                    document_id=doc_id,
                    revision_id=rev_id,
                    source_uri=uri,
                    content_hash=content_hash,
                    chunk_ids=prev_entry.chunk_ids,
                    state=DeltaState.MODIFIED,
                    reason=DeltaReason.MOVED,
                )
            else:
                results[uri] = ManifestEntry(
                    document_id=doc_id,
                    revision_id=rev_id,
                    source_uri=uri,
                    content_hash=content_hash,
                    state=DeltaState.NEW,
                    reason=DeltaReason.CREATED,
                )

    # Any remaining un-processed previous entries are DELETED
    for uri, prev_entry in prev_entries.items():
        if uri not in processed_prev_uris and uri not in current_files:
            results[uri] = ManifestEntry(
                document_id=prev_entry.document_id,
                revision_id=prev_entry.revision_id,
                source_uri=uri,
                content_hash=prev_entry.content_hash,
                chunk_ids=prev_entry.chunk_ids,
                state=DeltaState.DELETED,
                reason=DeltaReason.REMOVED,
            )

    return results
