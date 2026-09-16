from __future__ import annotations

"""MDPipeline: Universal Enterprise Knowledge Infrastructure Core Runner.

Phase 0C Implementation: Orchestrates file discovery, delta lifecycle evaluation,
multi-language converter dispatch, security redaction, canonical SemanticDocument
construction, manifest tombstone updating, and error isolation.
"""

from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple
import uuid

from md_generator.lineage.ids import (
    compute_content_hash,
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
from md_generator.metadata.schema import EnterpriseMetadata
from md_generator.pipeline.config import PipelineConfig
from md_generator.pipeline.registry import (
    ConverterAdapter,
    ConverterRegistry,
    ExtractionOutput,
    UnsupportedSourceError,
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
    ) -> None:
        self.config = config or PipelineConfig()
        self.registry = registry or ConverterRegistry.create_default()
        self.redactor = SecurityRedactor(policy=self.config.security_policy)

    def process_file(
        self, file_path: str, source_type: Optional[str] = None
    ) -> IngestionResult:
        """Process a single file through the pipeline.

        Evaluates NEW, MODIFIED, UNCHANGED, FAILED (cannot evaluate DELETED without directory scope).
        """
        start_time = time.time()
        path = Path(file_path).resolve()
        source_uri = normalize_source_uri(str(path))
        config_fp = self.config.compute_fingerprint()

        # Resolve adapter first to get accurate source_type
        try:
            adapter = self.registry.resolve(str(path), source_type=source_type)
            resolved_source_type = source_type or getattr(adapter, "_source_type", "text.plain")
        except Exception:
            resolved_source_type = source_type or "text.plain"

        # Build current file entry for delta engine
        content_text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        c_hash = compute_content_hash(content_text)
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
        delta_map = evaluate_delta(self.config.manifest, current_files, config_fp)

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

                # Create Enterprise Metadata
                ent_meta = EnterpriseMetadata(
                    tenant=self.config.tenant,
                    repository=self.config.repository,
                    source_uri=norm_extracted_uri,
                    source_type=extraction.source_type,
                )
                meta_dict = ent_meta.to_dict()
                if self.config.commit:
                    meta_dict["commit"] = self.config.commit
                if self.config.extra_metadata:
                    meta_dict["extra_metadata"] = self.config.extra_metadata

                # Build SemanticDocument v1.0
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
            timestamp=time.time(),
            entries=out_manifest_entries,
        )

        # Stage hooks (disabled/no-op in 0C)
        chunks = self._chunking_stage(documents)
        entities, relationships = self._graph_stage(chunks)
        self._embedding_stage(chunks)

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
        source_root_uri = normalize_source_uri(str(dir_path))
        config_fp = self.config.compute_fingerprint()

        # Discover all files in target directory
        discovered_files: List[Path] = []
        if dir_path.exists() and dir_path.is_dir():
            for p in dir_path.rglob("*"):
                if p.is_file() and not p.name.startswith("."):
                    discovered_files.append(p.resolve())

        current_files: Dict[str, Dict[str, Any]] = {}
        file_adapters: Dict[str, Tuple[Path, str]] = {}

        for p in discovered_files:
            uri = normalize_source_uri(str(p))
            try:
                adapter = self.registry.resolve(str(p))
                src_type = getattr(adapter, "_source_type", "text.plain")
            except Exception:
                src_type = "text.plain"

            content_text = p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""
            c_hash = compute_content_hash(content_text)
            d_id = generate_document_id(uri, src_type, self.config.repository)
            r_id = generate_revision_id(d_id, c_hash, self.config.commit, config_fp)

            current_files[uri] = {
                "document_id": d_id,
                "content_hash": c_hash,
                "revision_id": r_id,
            }
            file_adapters[uri] = (p, src_type)

        # Run Delta Engine
        delta_map = evaluate_delta(self.config.manifest, current_files, config_fp)

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

                    ent_meta = EnterpriseMetadata(
                        tenant=self.config.tenant,
                        repository=self.config.repository,
                        source_uri=norm_extracted_uri,
                        source_type=extraction.source_type,
                    )
                    meta_dict = ent_meta.to_dict()
                    if self.config.commit:
                        meta_dict["commit"] = self.config.commit
                    if self.config.extra_metadata:
                        meta_dict["extra_metadata"] = self.config.extra_metadata

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
            timestamp=time.time(),
            entries=out_manifest_entries,
        )

        chunks = self._chunking_stage(documents)
        entities, relationships = self._graph_stage(chunks)
        self._embedding_stage(chunks)

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
    # Extension Stage Hooks (Disabled / No-Op in Phase 0C)
    # ------------------------------------------------------------------

    def _chunking_stage(self, documents: List[SemanticDocument]) -> List[SemanticChunk]:
        """Disabled / pass-through in 0C; populated in Phase 1A with Tree-sitter chunkers."""
        return []

    def _embedding_stage(self, chunks: List[SemanticChunk]) -> None:
        """Disabled / pass-through in 0C; populated in Phase 1B with Vector Providers."""
        pass

    def _graph_stage(
        self, chunks: List[SemanticChunk]
    ) -> Tuple[List[Entity], List[Relationship]]:
        """Disabled / pass-through in 0C; populated in Phase 2C with GraphRAG."""
        return ([], [])
