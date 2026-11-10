from __future__ import annotations

"""IngestionResult, IngestionStatistics & IngestionError contracts.

Phase 0C-1 Implementation: Execution result dataclasses, UUID4 run_id,
and deterministic scope & request execution fingerprint.
"""

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Dict, List
import uuid

from md_generator.lineage.manifest import VersionedManifest
from md_generator.semantic.model.schema import Entity, Relationship, SemanticChunk, SemanticDocument
from md_generator.pipeline.sanitizer import TracebackSanitizer


@dataclass
class IngestionError:
    """Represents a partial processing error for a specific source URI."""

    source_uri: str
    error_type: str
    message: str
    traceback: str

    def __post_init__(self) -> None:
        """Sanitize traceback automatically upon initialization."""
        self.traceback = TracebackSanitizer.sanitize(self.traceback)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_uri": self.source_uri,
            "error_type": self.error_type,
            "message": self.message,
            "traceback": self.traceback,
        }


@dataclass
class IngestionStatistics:
    """Execution statistics counters for pipeline observability."""

    total_discovered: int = 0
    processed_count: int = 0
    unchanged_count: int = 0
    failed_count: int = 0
    deleted_count: int = 0
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_discovered": self.total_discovered,
            "processed_count": self.processed_count,
            "unchanged_count": self.unchanged_count,
            "failed_count": self.failed_count,
            "deleted_count": self.deleted_count,
            "duration_seconds": round(self.duration_seconds, 6),
        }


def compute_execution_fingerprint(
    config_fingerprint: str,
    operation: str,
    source_root: str,
    document_identities: List[Dict[str, str]],
) -> str:
    """Compute deterministic SHA-256 fingerprint representing logical request state and scope.

    document_identities maps: [{"document_id": id, "revision_id": rev}, ...]
    """
    sorted_docs = sorted(
        document_identities,
        key=lambda d: (d.get("document_id", ""), d.get("revision_id", "")),
    )
    data = {
        "config_fingerprint": config_fingerprint,
        "documents": sorted_docs,
        "scope": {
            "operation": operation,
            "source_root": source_root.replace("\\", "/").strip(),
        },
    }
    raw_json = json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(raw_json.encode("utf-8")).hexdigest()


@dataclass
class IngestionResult:
    """Result of an MDPipeline execution run."""

    run_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    execution_fingerprint: str = ""
    config_fingerprint: str = ""
    documents: List[SemanticDocument] = field(default_factory=list)
    chunks: List[SemanticChunk] = field(default_factory=list)
    entities: List[Entity] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    statistics: IngestionStatistics = field(default_factory=IngestionStatistics)
    errors: List[IngestionError] = field(default_factory=list)
    manifest: VersionedManifest = field(default_factory=VersionedManifest)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "execution_fingerprint": self.execution_fingerprint,
            "config_fingerprint": self.config_fingerprint,
            "documents": [d.to_dict() for d in self.documents],
            "chunks": [c.to_dict() for c in self.chunks],
            "entities": [e.to_dict() for e in self.entities],
            "relationships": [r.to_dict() for r in self.relationships],
            "statistics": self.statistics.to_dict(),
            "errors": [err.to_dict() for err in self.errors],
            "manifest": self.manifest.to_dict(),
        }
