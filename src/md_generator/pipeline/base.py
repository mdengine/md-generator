from __future__ import annotations

"""MDPipeline: Universal Enterprise Knowledge Infrastructure Core Runner.

Phase 0C Implementation: Orchestrates file discovery, delta lifecycle evaluation,
multi-language converter dispatch, security redaction, canonical SemanticDocument
construction, manifest tombstone updating, and error isolation.
"""

from pathlib import Path
import os
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

from md_generator.lineage.ids import (
    compute_content_hash,
    compute_file_content_hash,
    generate_document_id,
    generate_revision_id,
    normalize_source_uri,
)
from md_generator.lineage.manifest import (
    DeltaReason,
    DeltaState,
    ManifestEntry,
    VersionedManifest,
    evaluate_delta,
)
from md_generator.pipeline.config import PipelineConfig
from md_generator.pipeline.registry import (
    ConverterAdapter,
    ConverterRegistry,
    ExtractionOutput,
    UnsupportedSourceError,
    MissingDependencyError,
    IngestionDiscoveryError,
)
from md_generator.pipeline.result import (
    IngestionError,
    IngestionResult,
    IngestionStatistics,
    compute_execution_fingerprint,
)
from md_generator.security.redactor import SecurityRedactor
from md_generator.semantic.model.schema import (
    CanonicalMetadata,
    DocumentLineage,
    Entity,
    Relationship,
    SemanticChunk,
    SemanticDocument,
    SourceLocation,
)


class MDPipeline:
    """Universal Enterprise Knowledge Infrastructure Layer Orchestrator."""

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        registry: Optional[ConverterRegistry] = None,
        chunker: Optional[Any] = None,
        embedding_processor: Optional[Any] = None,
        graph_store: Optional[Any] = None,
    ) -> None:
        self.config = config or PipelineConfig()
        if not self.config.tenant or not isinstance(self.config.tenant, str) or not self.config.tenant.strip():
            from md_generator.vector.exceptions import TenantBoundaryError
            raise TenantBoundaryError("A valid non-empty tenant identifier is mandatory for MDPipeline.")
        self.registry = registry or ConverterRegistry.create_default()
        self.redactor = SecurityRedactor(policy=self.config.security_policy)
        self.chunker = chunker
        self.embedding_processor = embedding_processor
        self.graph_store = graph_store

    def process_file(
        self, file_path: str, source_type: Optional[str] = None
    ) -> IngestionResult:
        """Process a single file through the pipeline.

        Evaluates NEW, MODIFIED, UNCHANGED, FAILED (cannot evaluate DELETED without directory scope).
        """
        start_time = time.time()
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Target file does not exist: {path}")
        if not path.is_file():
            raise IsADirectoryError(f"Target is a directory, not a regular file: {path}")
        source_uri = normalize_source_uri(str(path))
        config_fp = self.config.compute_fingerprint()

        # Resolve adapter first to get accurate source_type
        try:
            adapter = self.registry.resolve(str(path), source_type=source_type)
            resolved_source_type = source_type or getattr(adapter, "_source_type", "text.plain")
        except Exception:
            resolved_source_type = source_type or "text.plain"

        # Build current file entry for delta engine using deterministic byte-based hashing
        c_hash = compute_file_content_hash(path)
        doc_id = generate_document_id(source_uri, resolved_source_type, self.config.repository)
        raw_rev_id = generate_revision_id(doc_id, c_hash, self.config.commit, config_fp)

        current_files = {
            source_uri: {
                "document_id": doc_id,
                "content_hash": c_hash,
                "revision_id": raw_rev_id,
            }
        }

        # Run Delta Engine against input manifest
        delta_map = evaluate_delta(
            self.config.manifest,
            current_files,
            current_config_hash=config_fp,
            current_tenant=self.config.tenant,
        )

        documents: List[SemanticDocument] = []
        errors: List[IngestionError] = []
        doc_identities: List[Dict[str, str]] = []
        out_manifest_entries: Dict[str, ManifestEntry] = {}

        if self.config.manifest and self.config.manifest.entries:
            out_manifest_entries.update(self.config.manifest.entries)

        stats = IngestionStatistics(total_discovered=1)

        delta_entry = delta_map.get(source_uri)
        state = delta_entry.state if delta_entry else DeltaState.NEW

        # Check if extraction can be skipped
        if state == DeltaState.UNCHANGED and self.config.enable_delta_sync:
            stats.unchanged_count += 1
            prev_entry = self.config.manifest.entries[source_uri] if self.config.manifest and source_uri in self.config.manifest.entries else None
            effective_doc_id = prev_entry.document_id if prev_entry else doc_id
            effective_rev_id = prev_entry.revision_id if prev_entry else raw_rev_id
            doc_identities.append(
                {"document_id": effective_doc_id, "revision_id": effective_rev_id}
            )
            if prev_entry:
                out_manifest_entries[source_uri] = prev_entry
        else:
            # Perform Extraction, Normalization & Security Redaction
            try:
                adapter = self.registry.resolve(str(path), source_type=source_type)
                extraction = adapter.extract(str(path))

                # Apply Security Redactor
                redaction_res = self.redactor.redact(extraction.raw_markdown)

                norm_extracted_uri = normalize_source_uri(extraction.source_uri)
                final_content_hash = compute_content_hash(redaction_res.sanitized_content)
                final_doc_id = generate_document_id(
                    norm_extracted_uri, extraction.source_type, self.config.repository
                )
                final_rev_id = generate_revision_id(
                    final_doc_id, final_content_hash, self.config.commit, config_fp
                )

                # Build SemanticDocument v1.0 (Phase 0A schema preserved intact)
                canon_meta = CanonicalMetadata(
                    source_uri=norm_extracted_uri,
                    source_type=extraction.source_type,
                    repository=self.config.repository if self.config.repository else None,
                    commit=self.config.commit if self.config.commit else None,
                )
                doc_lineage = DocumentLineage(
                    source_hash=final_content_hash,
                    created_timestamp=time.time(),
                )
                sem_doc = SemanticDocument(
                    document_id=final_doc_id,
                    sanitized_content=redaction_res.sanitized_content,
                    document_type="generic",
                    metadata=canon_meta,
                    lineage=doc_lineage,
                    security=redaction_res.metadata,
                )

                documents.append(sem_doc)
                stats.processed_count += 1
                doc_identities.append(
                    {"document_id": final_doc_id, "revision_id": final_rev_id}
                )

                # Update Manifest Entry
                out_manifest_entries[source_uri] = ManifestEntry(
                    document_id=final_doc_id,
                    revision_id=final_rev_id,
                    source_uri=source_uri,
                    content_hash=c_hash,
                    last_processed_timestamp=time.time(),
                    state=DeltaState.NEW if state == DeltaState.NEW else DeltaState.MODIFIED,
                    reason=DeltaReason.CREATED if state == DeltaState.NEW else DeltaReason.CONTENT_CHANGED,
                )

            except Exception as ex:
                import traceback

                stats.failed_count += 1
                tb_str = traceback.format_exc()
                err = IngestionError(
                    source_uri=source_uri,
                    error_type=type(ex).__name__,
                    message=str(ex),
                    traceback=tb_str,
                )
                errors.append(err)

                prev_entry = self.config.manifest.entries.get(source_uri) if self.config.manifest else None
                out_manifest_entries[source_uri] = ManifestEntry(
                    document_id=prev_entry.document_id if prev_entry else doc_id,
                    revision_id=prev_entry.revision_id if prev_entry else raw_rev_id,
                    source_uri=source_uri,
                    content_hash=prev_entry.content_hash if prev_entry else c_hash,
                    last_processed_timestamp=time.time(),
                    state=DeltaState.FAILED,
                    reason=DeltaReason.EXTRACTION_FAILED,
                    error_details={"error_type": type(ex).__name__, "message": str(ex)},
                )

        stats.duration_seconds = time.time() - start_time

        # Compute execution fingerprint
        exec_fp = compute_execution_fingerprint(
            config_fingerprint=config_fp,
            operation="process_file",
            source_root=source_uri,
            document_identities=doc_identities,
        )

        out_manifest = VersionedManifest(
            config_fingerprint=config_fp,
            tenant_id=self.config.tenant,
            timestamp=time.time(),
            entries=out_manifest_entries,
        )

        # Stage hooks with dependency injection & error isolation
        chunks = self._chunking_stage(documents)
        self._embedding_stage(chunks, documents, errors=errors, out_manifest_entries=out_manifest_entries)
        entities, relationships = self._graph_stage(chunks, documents, errors=errors, out_manifest_entries=out_manifest_entries)

        return IngestionResult(
            run_id=uuid.uuid4().hex,
            execution_fingerprint=exec_fp,
            config_fingerprint=config_fp,
            documents=documents,
            chunks=chunks,
            entities=entities,
            relationships=relationships,
            statistics=stats,
            errors=errors,
            manifest=out_manifest,
        )

    def process_directory(self, directory_path: str) -> IngestionResult:
        """Process an entire directory scope through the pipeline.

        Evaluates NEW, MODIFIED, UNCHANGED, FAILED, and DELETED tombstones.
        """
        start_time = time.time()
        dir_path = Path(directory_path).resolve()
        if not dir_path.exists():
            raise FileNotFoundError(f"Target directory does not exist: {dir_path}")
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Target path is not a directory: {dir_path}")

        source_root_uri = normalize_source_uri(str(dir_path))
        config_fp = self.config.compute_fingerprint()

        # Discover all files in target directory with traversal integrity check
        def _on_walk_error(err: OSError):
            raise IngestionDiscoveryError(f"Directory traversal failed at {err.filename}: {err}") from err

        discovered_files: List[Path] = []
        try:
            for root, dirs, files in os.walk(dir_path, onerror=_on_walk_error):
                for f in files:
                    if not f.startswith("."):
                        p = Path(root) / f
                        discovered_files.append(p.resolve())
        except IngestionDiscoveryError:
            raise
        except Exception as e:
            raise IngestionDiscoveryError(f"Directory discovery failed for {dir_path}: {e}") from e

        current_files: Dict[str, Dict[str, Any]] = {}
        file_adapters: Dict[str, Tuple[Path, str]] = {}

        for p in discovered_files:
            uri = normalize_source_uri(str(p))
            try:
                adapter = self.registry.resolve(str(p))
                src_type = getattr(adapter, "_source_type", "text.plain")
            except Exception:
                src_type = "text.plain"

            c_hash = compute_file_content_hash(p)
            d_id = generate_document_id(uri, src_type, self.config.repository)
            r_id = generate_revision_id(d_id, c_hash, self.config.commit, config_fp)

            current_files[uri] = {
                "document_id": d_id,
                "content_hash": c_hash,
                "revision_id": r_id,
            }
            file_adapters[uri] = (p, src_type)

        # Run Delta Engine
        delta_map = evaluate_delta(
            self.config.manifest,
            current_files,
            current_config_hash=config_fp,
            current_tenant=self.config.tenant,
        )

        documents: List[SemanticDocument] = []
        errors: List[IngestionError] = []
        doc_identities: List[Dict[str, str]] = []
        out_manifest_entries: Dict[str, ManifestEntry] = {}

        if self.config.manifest and self.config.manifest.entries:
            out_manifest_entries.update(self.config.manifest.entries)

        stats = IngestionStatistics(total_discovered=len(discovered_files))

        for uri, entry in delta_map.items():
            state = entry.state

            if state == DeltaState.DELETED:
                stats.deleted_count += 1
                out_manifest_entries[uri] = ManifestEntry(
                    document_id=entry.document_id,
                    revision_id=entry.revision_id,
                    source_uri=uri,
                    content_hash=entry.content_hash,
                    last_processed_timestamp=time.time(),
                    state=DeltaState.DELETED,
                    reason=DeltaReason.REMOVED,
                )
            elif state == DeltaState.UNCHANGED and self.config.enable_delta_sync:
                stats.unchanged_count += 1
                prev_entry = self.config.manifest.entries.get(uri) if self.config.manifest else None
                eff_doc_id = prev_entry.document_id if prev_entry else entry.document_id
                eff_rev_id = prev_entry.revision_id if prev_entry else entry.revision_id
                doc_identities.append({"document_id": eff_doc_id, "revision_id": eff_rev_id})
                if prev_entry:
                    out_manifest_entries[uri] = prev_entry
            else:
                # NEW, MODIFIED, or UNCHANGED with enable_delta_sync=False
                p_info = file_adapters.get(uri)
                p = p_info[0] if p_info else Path(uri.replace("file:///", "").replace("file://", ""))
                try:
                    adapter = self.registry.resolve(str(p))
                    extraction = adapter.extract(str(p))

                    redaction_res = self.redactor.redact(extraction.raw_markdown)

                    norm_extracted_uri = normalize_source_uri(extraction.source_uri)
                    final_content_hash = compute_content_hash(redaction_res.sanitized_content)
                    final_doc_id = generate_document_id(
                        norm_extracted_uri, extraction.source_type, self.config.repository
                    )
                    final_rev_id = generate_revision_id(
                        final_doc_id, final_content_hash, self.config.commit, config_fp
                    )

                    # Build SemanticDocument v1.0 (Phase 0A schema preserved intact)
                    canon_meta = CanonicalMetadata(
                        source_uri=norm_extracted_uri,
                        source_type=extraction.source_type,
                        repository=self.config.repository if self.config.repository else None,
                        commit=self.config.commit if self.config.commit else None,
                    )
                    doc_lineage = DocumentLineage(
                        source_hash=final_content_hash,
                        created_timestamp=time.time(),
                    )
                    sem_doc = SemanticDocument(
                        document_id=final_doc_id,
                        sanitized_content=redaction_res.sanitized_content,
                        document_type="generic",
                        metadata=canon_meta,
                        lineage=doc_lineage,
                        security=redaction_res.metadata,
                    )

                    documents.append(sem_doc)
                    stats.processed_count += 1
                    doc_identities.append(
                        {"document_id": final_doc_id, "revision_id": final_rev_id}
                    )

                    raw_c_hash = current_files[uri]["content_hash"] if uri in current_files else final_content_hash
                    out_manifest_entries[uri] = ManifestEntry(
                        document_id=final_doc_id,
                        revision_id=final_rev_id,
                        source_uri=uri,
                        content_hash=raw_c_hash,
                        last_processed_timestamp=time.time(),
                        state=DeltaState.NEW if state == DeltaState.NEW else DeltaState.MODIFIED,
                        reason=DeltaReason.CREATED if state == DeltaState.NEW else DeltaReason.CONTENT_CHANGED,
                    )
                except Exception as ex:
                    import traceback

                    stats.failed_count += 1
                    tb_str = traceback.format_exc()
                    err = IngestionError(
                        source_uri=uri,
                        error_type=type(ex).__name__,
                        message=str(ex),
                        traceback=tb_str,
                    )
                    errors.append(err)

                    prev_entry = self.config.manifest.entries.get(uri) if self.config.manifest else None
                    out_manifest_entries[uri] = ManifestEntry(
                        document_id=prev_entry.document_id if prev_entry else entry.document_id,
                        revision_id=prev_entry.revision_id if prev_entry else entry.revision_id,
                        source_uri=uri,
                        content_hash=prev_entry.content_hash if prev_entry else entry.content_hash,
                        last_processed_timestamp=time.time(),
                        state=DeltaState.FAILED,
                        reason=DeltaReason.EXTRACTION_FAILED,
                        error_details={"error_type": type(ex).__name__, "message": str(ex)},
                    )

        stats.duration_seconds = time.time() - start_time

        exec_fp = compute_execution_fingerprint(
            config_fingerprint=config_fp,
            operation="process_directory",
            source_root=source_root_uri,
            document_identities=doc_identities,
        )

        out_manifest = VersionedManifest(
            config_fingerprint=config_fp,
            tenant_id=self.config.tenant,
            timestamp=time.time(),
            entries=out_manifest_entries,
        )

        chunks = self._chunking_stage(documents)
        self._embedding_stage(chunks, documents, errors=errors, out_manifest_entries=out_manifest_entries)
        entities, relationships = self._graph_stage(chunks, documents, errors=errors, out_manifest_entries=out_manifest_entries)

        return IngestionResult(
            run_id=uuid.uuid4().hex,
            execution_fingerprint=exec_fp,
            config_fingerprint=config_fp,
            documents=documents,
            chunks=chunks,
            entities=entities,
            relationships=relationships,
            statistics=stats,
            errors=errors,
            manifest=out_manifest,
        )

    # ------------------------------------------------------------------
    # Extension Stage Hooks & Atomic Manifest Persistence
    # ------------------------------------------------------------------

    def _chunking_stage(self, documents: List[SemanticDocument]) -> List[SemanticChunk]:
        """Orchestrate Phase 1A semantic chunking if chunker is configured."""
        if self.chunker is not None and documents:
            if hasattr(self.chunker, "process_documents"):
                res = self.chunker.process_documents(documents)
                return getattr(res, "chunks", [])
            elif hasattr(self.chunker, "chunk_document"):
                all_chunks: List[SemanticChunk] = []
                for doc in documents:
                    all_chunks.extend(self.chunker.chunk_document(doc))
                return all_chunks
        return []

    def _embedding_stage(
        self,
        chunks: List[SemanticChunk],
        documents: Optional[List[SemanticDocument]] = None,
        errors: Optional[List[IngestionError]] = None,
        out_manifest_entries: Optional[Dict[str, ManifestEntry]] = None,
    ) -> None:
        """Orchestrate Phase 1B vector synchronization if embedding processor is configured."""
        if self.embedding_processor is not None and chunks:
            if hasattr(self.embedding_processor, "sync_semantic_result"):
                from md_generator.semantic.processor import SemanticProcessingResult
                sem_res = SemanticProcessingResult(
                    chunks=chunks,
                    entities=[],
                    relationships=[],
                    diagnostics=[],
                    semantic_processing_fingerprint="",
                )
                try:
                    self.embedding_processor.sync_semantic_result(sem_res, tenant_id=self.config.tenant)
                except Exception as e:
                    if errors is not None:
                        errors.append(
                            IngestionError(
                                source_uri="vector_sync",
                                error_type=type(e).__name__,
                                message=f"Vector sync failed: {e}",
                                traceback="",
                            )
                        )
                    if out_manifest_entries is not None and documents:
                        for doc in documents:
                            uri = doc.metadata.source_uri if doc.metadata else ""
                            if uri in out_manifest_entries:
                                entry = out_manifest_entries[uri]
                                out_manifest_entries[uri] = ManifestEntry(
                                    document_id=entry.document_id,
                                    revision_id=entry.revision_id,
                                    source_uri=entry.source_uri,
                                    content_hash=entry.content_hash,
                                    state=DeltaState.FAILED,
                                    reason=DeltaReason.EXTRACTION_FAILED,
                                    error_details={"stage": "embedding", "error": str(e)},
                                )

    def _graph_stage(
        self,
        chunks: List[SemanticChunk],
        documents: Optional[List[SemanticDocument]] = None,
        errors: Optional[List[IngestionError]] = None,
        out_manifest_entries: Optional[Dict[str, ManifestEntry]] = None,
    ) -> Tuple[List[Entity], List[Relationship]]:
        """Orchestrate Phase 2C Knowledge Graph extraction if graph store is configured."""
        entities: List[Entity] = []
        relationships: List[Relationship] = []
        if self.graph_store is not None and documents:
            from md_generator.graph.extractor import extract
            for doc in documents:
                try:
                    doc_chunks = [c for c in chunks if getattr(c, "document_id", None) == doc.document_id]
                    kg = extract(doc, doc_chunks, tenant_id=self.config.tenant)
                    if hasattr(self.graph_store, "upsert_graph"):
                        self.graph_store.upsert_graph(kg, tenant_id=self.config.tenant)
                except Exception as e:
                    # Compensating rollback in vector store for already-synced document records
                    if self.embedding_processor is not None and hasattr(self.embedding_processor, "store"):
                        try:
                            if hasattr(self.embedding_processor.store, "delete_records_by_document_id"):
                                self.embedding_processor.store.delete_records_by_document_id(doc.document_id, self.config.tenant)
                        except Exception:
                            pass
                    if errors is not None:
                        errors.append(
                            IngestionError(
                                source_uri=doc.metadata.source_uri if doc.metadata else "unknown",
                                error_type=type(e).__name__,
                                message=f"Graph indexing failed: {e}",
                                traceback="",
                            )
                        )
                    if out_manifest_entries is not None:
                        uri = doc.metadata.source_uri if doc.metadata else ""
                        if uri in out_manifest_entries:
                            entry = out_manifest_entries[uri]
                            out_manifest_entries[uri] = ManifestEntry(
                                document_id=entry.document_id,
                                revision_id=entry.revision_id,
                                source_uri=entry.source_uri,
                                content_hash=entry.content_hash,
                                state=DeltaState.FAILED,
                                reason=DeltaReason.EXTRACTION_FAILED,
                                error_details={"stage": "graph", "error": str(e)},
                            )
        return (entities, relationships)

    @staticmethod
    def save_manifest_atomically(manifest: VersionedManifest, target_path: Union[Path, str]) -> None:
        """Atomically persist VersionedManifest to disk via temporary file rename."""
        p = Path(target_path).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = p.with_name(f".{p.name}.tmp.{uuid.uuid4().hex}")
        try:
            tmp_file.write_text(manifest.to_json(), encoding="utf-8")
            os.replace(tmp_file, p)
        except Exception:
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except OSError:
                    pass
            raise

    @staticmethod
    def clean_orphaned_manifest_tmps(dir_path: Union[Path, str], max_age_seconds: float = 3600.0) -> int:
        """Clean up orphaned temporary manifest files left by aborted processes."""
        d = Path(dir_path).resolve()
        if not d.exists() or not d.is_dir():
            return 0
        cleaned = 0
        now = time.time()
        for f in d.glob(".*.tmp.*"):
            if f.is_file():
                try:
                    if now - f.stat().st_mtime > max_age_seconds:
                        f.unlink()
                        cleaned += 1
                except OSError:
                    pass
        return cleaned
