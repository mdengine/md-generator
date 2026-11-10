"""EmbeddingProcessor engine, atomic manifest sync, secret-free fingerprinting, and reconciliation."""

import copy
import json
import time
import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from md_generator.semantic.model.schema import SemanticDocument
from md_generator.semantic.processor import SemanticProcessingResult
from md_generator.vector.exceptions import (
    VectorError,
    EmbeddingProviderError,
    VectorStoreError,
    CollectionConfigurationError,
    TenantBoundaryError,
)
from md_generator.vector.model import (
    CollectionConfig,
    EmbeddingRecord,
    VectorSyncRecord,
    VectorSyncManifest,
    VectorSyncManifestStore,
    EMBEDDING_ID_ALGORITHM_VERSION,
    manifest_document_key,
    manifest_record_key,
)
from md_generator.vector.providers.base import BaseEmbeddingProvider
from md_generator.vector.stores.base import BaseVectorStore

SECRET_PATTERNS: Set[str] = {
    "api_key",
    "access_token",
    "secret",
    "password",
    "authorization",
    "token",
    "bearer",
    "credentials",
    "key",
}


def sanitize_config_recursive(data: Any) -> Any:
    """Recursively strips keys matching normalized secret patterns from a config object copy."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if isinstance(k, str) and any(pat in k.lower() for pat in SECRET_PATTERNS):
                continue
            cleaned[k] = sanitize_config_recursive(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_config_recursive(item) for item in data]
    else:
        return data


def compute_embedding_processing_fingerprint(
    provider: BaseEmbeddingProvider,
    provider_config: Optional[Dict[str, Any]] = None,
    distance_metric: str = "cosine",
) -> str:
    """Computes a deterministic, secret-free SHA-256 fingerprint for provider configuration."""
    safe_config = sanitize_config_recursive(provider_config or {})
    payload = {
        "provider_name": provider.provider_name,
        "model_name": provider.model_name,
        "model_version": provider.model_version,
        "dimension": provider.dimension,
        "distance_metric": distance_metric,
        "config": safe_config,
    }
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def compute_embedding_id(
    chunk_id: str,
    provider_name: str,
    model_name: str,
    model_version: str,
) -> str:
    """Computes a canonical, collision-resistant embedding ID with algorithm versioning."""
    payload = {
        "algorithm_version": EMBEDDING_ID_ALGORITHM_VERSION,
        "chunk_id": chunk_id,
        "provider_name": provider_name,
        "model_name": model_name,
        "model_version": model_version,
    }
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


@dataclass
class VectorSyncResult:
    total_chunks: int = 0
    embedded_count: int = 0
    skipped_unchanged_count: int = 0
    failed_count: int = 0
    deleted_tombstones_count: int = 0
    upserted_records_count: int = 0
    diagnostics: Dict[str, Any] = field(default_factory=dict)


class EmbeddingProcessor:
    """Delta vector synchronization processor with atomic manifest persistence and recovery."""

    def __init__(
        self,
        provider: BaseEmbeddingProvider,
        store: BaseVectorStore,
        manifest_filepath: str,
        collection_name: str = "enterprise_knowledge",
        distance_metric: str = "cosine",
        provider_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.provider = provider
        self.store = store
        self.manifest_filepath = manifest_filepath
        self.collection_name = collection_name
        self.distance_metric = distance_metric
        self.provider_config = provider_config or {}

        # Initialize store collection immutably
        config = CollectionConfig(
            collection_name=collection_name,
            dimension=provider.dimension,
            distance_metric=distance_metric,
        )
        self.store.initialize_collection(config)

        # Load synchronization manifest
        self.manifest = VectorSyncManifestStore.load(manifest_filepath)

        # Compute provider embedding fingerprint
        self.embedding_processing_fingerprint = compute_embedding_processing_fingerprint(
            provider, self.provider_config, distance_metric
        )

    def _validate_tenant(self, tenant_id: str) -> None:
        if tenant_id is None or not isinstance(tenant_id, str) or tenant_id.strip() == "":
            raise TenantBoundaryError("A valid non-empty tenant_id is mandatory for vector processing.")

    def sync_semantic_result(
        self,
        semantic_result: SemanticProcessingResult,
        tenant_id: str,
    ) -> VectorSyncResult:
        """Synchronizes semantic processing chunks to vector store and atomic manifest."""
        self._validate_tenant(tenant_id)
        result = VectorSyncResult()

        if semantic_result is None or not hasattr(semantic_result, "chunks"):
            return result

        doc = getattr(semantic_result, "document", None)
        doc_id = getattr(doc, "document_id", None) if doc else None
        chunks = getattr(semantic_result, "chunks", []) or []
        if not doc_id and chunks:
            doc_id = getattr(chunks[0], "document_id", None)
        if not doc_id:
            doc_id = "unknown_doc"

        revision_id = getattr(doc, "revision_id", "v1") if doc else "v1"
        doc_fp = getattr(semantic_result, "semantic_processing_fingerprint", "") or getattr(semantic_result, "metadata", {}).get("semantic_processing_fingerprint", "default_doc_fp")
        result.total_chunks = len(chunks)

        if len(chunks) == 0:
            return result

        chunks_to_embed: List[Tuple[Any, str, str]] = []  # (chunk, chunk_fp, embedding_id)
        doc_key = manifest_document_key(tenant_id, doc_id)
        current_chunk_ids: List[str] = []

        for chunk in chunks:
            chunk_id = getattr(chunk, "chunk_id", "")
            if not chunk_id:
                continue
            current_chunk_ids.append(chunk_id)

            chunk_fp = getattr(chunk, "semantic_processing_fingerprint", doc_fp)
            emb_id = compute_embedding_id(
                chunk_id,
                self.provider.provider_name,
                self.provider.model_name,
                self.provider.model_version,
            )

            rec_key = manifest_record_key(tenant_id, self.collection_name, emb_id)
            existing_rec = self.manifest.records.get(rec_key)

            if (
                existing_rec is not None
                and existing_rec.document_semantic_processing_fingerprint == doc_fp
                and existing_rec.chunk_semantic_processing_fingerprint == chunk_fp
                and existing_rec.embedding_processing_fingerprint == self.embedding_processing_fingerprint
            ):
                result.skipped_unchanged_count += 1
            else:
                chunks_to_embed.append((chunk, chunk_fp, emb_id))

        if len(chunks_to_embed) == 0:
            # Update document to chunks mapping if needed
            self.manifest.document_to_chunks[doc_key] = current_chunk_ids
            VectorSyncManifestStore.save_atomic(self.manifest, self.manifest_filepath)
            return result

        # Split into sub-batches bounded by provider.max_batch_size
        max_batch = self.provider.max_batch_size
        for i in range(0, len(chunks_to_embed), max_batch):
            sub_batch = chunks_to_embed[i : i + max_batch]
            texts = [getattr(c[0], "sanitized_content", "") or "" for c in sub_batch]

            try:
                vectors = self.provider.embed_texts(texts)
            except Exception as e:
                result.failed_count += len(sub_batch)
                continue

            if len(vectors) != len(sub_batch):
                result.failed_count += len(sub_batch)
                continue

            records_to_upsert: List[EmbeddingRecord] = []
            sync_records_to_commit: List[Tuple[str, VectorSyncRecord]] = []

            for (chunk_obj, chunk_fp, emb_id), vector in zip(sub_batch, vectors):
                rec = EmbeddingRecord(
                    embedding_id=emb_id,
                    chunk_id=chunk_obj.chunk_id,
                    document_id=doc_id,
                    vector=vector,
                    dimension=self.provider.dimension,
                    provider_name=self.provider.provider_name,
                    model_name=self.provider.model_name,
                    model_version=self.provider.model_version,
                    sanitized_content=getattr(chunk_obj, "sanitized_content", ""),
                    semantic_key=getattr(chunk_obj, "semantic_key", "key"),
                    tenant_id=tenant_id,
                    entity_type=getattr(chunk_obj, "entity_type", None),
                    parent_chunk_id=getattr(chunk_obj, "parent_chunk_id", None),
                    source_location=getattr(chunk_obj, "source_location", None),
                    payload=getattr(chunk_obj, "payload", {}),
                )
                records_to_upsert.append(rec)

                rec_key = manifest_record_key(tenant_id, self.collection_name, emb_id)
                sync_rec = VectorSyncRecord(
                    tenant_id=tenant_id,
                    document_id=doc_id,
                    revision_id=revision_id,
                    document_semantic_processing_fingerprint=doc_fp,
                    chunk_id=chunk_obj.chunk_id,
                    chunk_semantic_processing_fingerprint=chunk_fp,
                    provider_name=self.provider.provider_name,
                    model_name=self.provider.model_name,
                    model_version=self.provider.model_version,
                    embedding_processing_fingerprint=self.embedding_processing_fingerprint,
                    embedding_id=emb_id,
                    collection_name=self.collection_name,
                    created_timestamp=time.time(),
                )
                sync_records_to_commit.append((rec_key, sync_rec))

            # Store Upsert State Machine (M1 & P5)
            try:
                upserted_count = self.store.upsert_records(records_to_upsert, tenant_id)
            except Exception:
                result.failed_count += len(sub_batch)
                continue

            if upserted_count == len(records_to_upsert):
                # FULL CONFIRMATION: commit records to manifest
                for key, s_rec in sync_records_to_commit:
                    self.manifest.records[key] = s_rec
                result.embedded_count += len(sub_batch)
                result.upserted_records_count += upserted_count
            else:
                # UNCONFIRMED / PARTIAL: Zero direct manifest commits for this sub-batch
                result.failed_count += len(sub_batch)

        self.manifest.document_to_chunks[doc_key] = current_chunk_ids
        VectorSyncManifestStore.save_atomic(self.manifest, self.manifest_filepath)
        return result

    def purge_document_tombstones(self, document_id: str, tenant_id: str) -> int:
        """Purges vectors for a deleted document; enforces store deletion BEFORE manifest removal."""
        self._validate_tenant(tenant_id)

        # 1. Execute vector store tombstone purge
        deleted_count = self.store.delete_records_by_document_id(document_id, tenant_id)

        # 2. ONLY AFTER store deletion succeeds, purge active manifest entries
        doc_key = manifest_document_key(tenant_id, document_id)
        chunk_ids = self.manifest.document_to_chunks.get(doc_key, [])

        keys_to_remove = []
        for r_key, r_val in self.manifest.records.items():
            if r_val.tenant_id == tenant_id and r_val.document_id == document_id:
                keys_to_remove.append(r_key)

        for k in keys_to_remove:
            del self.manifest.records[k]

        if doc_key in self.manifest.document_to_chunks:
            del self.manifest.document_to_chunks[doc_key]

        VectorSyncManifestStore.save_atomic(self.manifest, self.manifest_filepath)
        return deleted_count

    def reconcile_unconfirmed_vectors(
        self, tenant_id: str, candidates: List[Tuple[str, VectorSyncRecord]]
    ) -> int:
        """Reconciles unconfirmed store records via contains_embedding_ids."""
        self._validate_tenant(tenant_id)
        if not candidates:
            return 0

        target_ids = [c[1].embedding_id for c in candidates]
        confirmed_ids = self.store.contains_embedding_ids(target_ids, tenant_id)

        reconciled_count = 0
        for key, s_rec in candidates:
            if s_rec.embedding_id in confirmed_ids:
                self.manifest.records[key] = s_rec
                reconciled_count += 1

        if reconciled_count > 0:
            VectorSyncManifestStore.save_atomic(self.manifest, self.manifest_filepath)

        return reconciled_count
