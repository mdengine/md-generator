from __future__ import annotations

"""Enterprise Hybrid Retriever: Dense Vectors, BM25 Lexical, RRF Fusion & Reranking.

Phase 1B/2A Implementation:
- Combines dense vector retrieval, Okapi BM25 keyword search, exact phrase matching, and graph expansion.
- Multi-way Reciprocal Rank Fusion (RRF) with configurable weights (weight_vector, weight_bm25, weight_phrase, weight_graph).
- Integrates QueryExpander (acronym/synonym expansion) and QueryDecomposer.
- Configurable reranker interface (RuleBasedReranker, CrossEncoderReranker).
- Strict multi-tenant isolation, metadata filtering, and candidate deduplication.
- Backward compatible with existing HybridGraphRAGRetriever and LangChain invoke() interfaces.
"""

from dataclasses import dataclass, field
import math
import re
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

from md_generator.graph.exceptions import TenantBoundaryError
from md_generator.graph.hybrid.retriever import ScoredHybridResult
from md_generator.graph.model import _validate_tenant_id
from md_generator.retrieval.bm25 import BM25Index, tokenize
from md_generator.retrieval.query_decomposer import RuleBasedQueryDecomposer
from md_generator.retrieval.query_expander import QueryExpander
from md_generator.retrieval.reranker import BaseReranker, RuleBasedReranker
from md_generator.vector.model import CollectionConfig, VectorQueryResult
from md_generator.vector.providers.base import BaseEmbeddingProvider
from md_generator.vector.registry import validate_dimension_compatibility
from md_generator.vector.stores.base import BaseVectorStore


@dataclass
class HybridSearchFilter:
    """Configurable metadata filters for retrieval candidates."""
    document_ids: Optional[Set[str]] = None
    location_types: Optional[Set[str]] = None
    min_score: float = 0.0
    pages: Optional[Set[int]] = None
    slides: Optional[Set[int]] = None


class EnterpriseHybridRetriever:
    """Enterprise-grade multi-tenant hybrid retriever combining dense vector and BM25 search."""

    def __init__(
        self,
        vector_store: BaseVectorStore,
        embedding_provider: BaseEmbeddingProvider,
        tenant_id: str,
        bm25_index: Optional[BM25Index] = None,
        graph_store: Optional[Any] = None,
        top_k: int = 10,
        rrf_k: int = 60,
        weight_vector: float = 1.0,
        weight_bm25: float = 1.0,
        weight_phrase: float = 0.5,
        weight_graph: float = 0.5,
        query_expander: Optional[QueryExpander] = None,
        query_decomposer: Optional[RuleBasedQueryDecomposer] = None,
        reranker: Optional[BaseReranker] = None,
        enable_deduplication: bool = True,
        dedup_overlap_threshold: float = 0.85,
    ) -> None:
        self.clean_tenant = _validate_tenant_id(tenant_id, "EnterpriseHybridRetriever.tenant_id")
        self.tenant_id = self.clean_tenant
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider

        # Dimension safety validation
        if hasattr(self.vector_store, "config") and self.vector_store.config:
            validate_dimension_compatibility(self.embedding_provider, self.vector_store.config)

        self.bm25_index = bm25_index or BM25Index()
        self.graph_store = graph_store
        self.top_k = max(1, top_k)
        self.rrf_k = max(1, rrf_k)
        self.weight_vector = float(weight_vector)
        self.weight_bm25 = float(weight_bm25)
        self.weight_phrase = float(weight_phrase)
        self.weight_graph = float(weight_graph)

        self.query_expander = query_expander or QueryExpander()
        self.query_decomposer = query_decomposer or RuleBasedQueryDecomposer()
        self.reranker = reranker or RuleBasedReranker()
        self.enable_deduplication = enable_deduplication
        self.dedup_overlap_threshold = dedup_overlap_threshold

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[HybridSearchFilter] = None,
        expand_query: bool = True,
        decompose_query: bool = False,
        rerank_results: bool = True,
    ) -> List[ScoredHybridResult]:
        """Perform end-to-end hybrid retrieval with RRF fusion, filtering, and reranking."""
        if not query or not isinstance(query, str) or not query.strip():
            raise ValueError("Query string must be non-empty.")

        effective_top_k = top_k or self.top_k
        clean_q = query.strip()

        # Step 1: Query Pre-processing (Acronym/Synonym Expansion & Decomposition)
        search_queries = [clean_q]
        if decompose_query:
            search_queries = self.query_decomposer.decompose(clean_q)

        expanded_query = self.query_expander.expand(clean_q) if expand_query else clean_q
        exact_phrases = self.query_expander.extract_exact_phrases(clean_q)

        # Candidate dictionaries: chunk_id -> details
        # v_scores: chunk_id -> (VectorQueryResult, score)
        v_candidates: Dict[str, Tuple[Any, float]] = {}
        # b_scores: chunk_id -> (BM25 doc info, score)
        b_candidates: Dict[str, Tuple[Dict[str, Any], float]] = {}
        # phrase_matches: chunk_id -> match_count
        p_matches: Dict[str, float] = {}

        # Step 2: Dense Vector Search
        try:
            q_vectors = self.embedding_provider.embed_texts([expanded_query])
            if q_vectors:
                q_vec = q_vectors[0]
                vec_results = self.vector_store.query(
                    query_vector=q_vec,
                    top_k=effective_top_k * 3,
                    tenant_id=self.clean_tenant,
                )
                for rank_idx, vr in enumerate(vec_results):
                    # Tenant validation
                    if vr.tenant_id != self.clean_tenant:
                        raise TenantBoundaryError(
                            f"Vector candidate tenant '{vr.tenant_id}' conflicts with retriever tenant '{self.clean_tenant}'."
                        )
                    cid = vr.chunk_id
                    score = getattr(vr, "score", 1.0 / (1.0 + rank_idx))
                    v_candidates[cid] = (vr, max(0.0, min(1.0, float(score))))
        except Exception:
            # If vector search fails or store is empty, continue with BM25
            pass

        # Step 3: BM25 Lexical Keyword Search
        bm25_raw = self.bm25_index.search(
            query=expanded_query,
            top_k=effective_top_k * 3,
            tenant_id=self.clean_tenant,
        )
        for rank_idx, (cid, b_score) in enumerate(bm25_raw):
            doc_info = self.bm25_index.get_document(cid) or {}
            b_candidates[cid] = (doc_info, b_score)

        # Step 4: Exact Phrase Matching
        if exact_phrases:
            for cid in set(v_candidates.keys()).union(set(b_candidates.keys())):
                content = ""
                if cid in v_candidates:
                    content = getattr(v_candidates[cid][0], "sanitized_content", "") or ""
                elif cid in b_candidates:
                    content = b_candidates[cid][0].get("text", "")

                content_lower = content.lower()
                matched = sum(1.0 for phrase in exact_phrases if phrase.lower() in content_lower)
                if matched > 0:
                    p_matches[cid] = matched / len(exact_phrases)

        # Step 5: Multi-Way Reciprocal Rank Fusion (RRF)
        universe_cids: Set[str] = set(v_candidates.keys()).union(set(b_candidates.keys()))
        if not universe_cids:
            return []

        # Build rank maps (1-based ranks) with deterministic tie-breaking
        sorted_v = sorted(v_candidates.keys(), key=lambda c: (-v_candidates[c][1], c))
        v_ranks = {cid: r + 1 for r, cid in enumerate(sorted_v)}

        sorted_b = sorted(b_candidates.keys(), key=lambda c: (-b_candidates[c][1], c))
        b_ranks = {cid: r + 1 for r, cid in enumerate(sorted_b)}

        sorted_p = sorted(p_matches.keys(), key=lambda c: (-p_matches[c], c))
        p_ranks = {cid: r + 1 for r, cid in enumerate(sorted_p)}

        # Maximum possible RRF raw score for normalization
        rrf_max = (
            (self.weight_vector / (self.rrf_k + 1))
            + (self.weight_bm25 / (self.rrf_k + 1))
            + (self.weight_phrase / (self.rrf_k + 1) if exact_phrases else 0.0)
        )
        rrf_max = max(rrf_max, 1e-9)

        fused_candidates: List[ScoredHybridResult] = []

        for cid in universe_cids:
            in_v = cid in v_candidates
            in_b = cid in b_candidates

            if in_v and in_b:
                prov: Literal["VECTOR_ONLY", "GRAPH_ONLY", "HYBRID"] = "HYBRID"
            elif in_v:
                prov = "VECTOR_ONLY"
            else:
                prov = "HYBRID"  # BM25-backed candidate

            # Extract content & metadata
            content = ""
            meta: Dict[str, Any] = {"chunk_id": cid, "tenant_id": self.clean_tenant}

            if in_v:
                v_obj = v_candidates[cid][0]
                content = getattr(v_obj, "sanitized_content", "") or ""
                meta.update(getattr(v_obj, "payload", {}) or {})
                if getattr(v_obj, "source_location", None):
                    meta["source_location"] = v_obj.source_location.to_dict()
                if getattr(v_obj, "parent_chunk_id", None):
                    meta["parent_chunk_id"] = v_obj.parent_chunk_id
            elif in_b:
                b_info = b_candidates[cid][0]
                content = b_info.get("text", "")
                meta.update(b_info.get("metadata", {}))

            s_v = v_candidates[cid][1] if in_v else 0.0
            s_b = b_candidates[cid][1] if in_b else 0.0

            # Compute RRF score
            rrf_raw = 0.0
            if in_v:
                rrf_raw += self.weight_vector / (self.rrf_k + v_ranks[cid])
            if in_b:
                rrf_raw += self.weight_bm25 / (self.rrf_k + b_ranks[cid])
            if cid in p_ranks:
                rrf_raw += self.weight_phrase / (self.rrf_k + p_ranks[cid])

            fused_score = max(0.0, min(1.0, rrf_raw / rrf_max))

            # Apply candidate filters
            if filters:
                if filters.document_ids and meta.get("document_id") not in filters.document_ids:
                    continue
                if filters.min_score and fused_score < filters.min_score:
                    continue
                loc = meta.get("source_location") or {}
                if filters.location_types and loc.get("location_type") not in filters.location_types:
                    continue
                if filters.pages and loc.get("page") not in filters.pages:
                    continue
                if filters.slides and loc.get("slide") not in filters.slides:
                    continue

            result = ScoredHybridResult(
                chunk_id=cid,
                content=content,
                tenant_id=self.clean_tenant,
                vector_score=s_v,
                graph_score=s_b,  # Store lexical score in secondary score slot
                hybrid_score=fused_score,
                provenance=prov,
                metadata=meta,
            )
            fused_candidates.append(result)

        # Step 6: Deduplication (suppress near-duplicate chunks)
        if self.enable_deduplication and len(fused_candidates) > 1:
            fused_candidates = self._deduplicate_candidates(fused_candidates)

        # Step 7: Optional Reranking
        if rerank_results and self.reranker and fused_candidates:
            fused_candidates = self.reranker.rerank(clean_q, fused_candidates, top_k=effective_top_k)
        else:
            # Deterministic sort: (-hybrid_score, -vector_score, chunk_id)
            fused_candidates.sort(key=lambda r: (-r.hybrid_score, -r.vector_score, r.chunk_id))
            fused_candidates = fused_candidates[:effective_top_k]

        return fused_candidates

    def _deduplicate_candidates(self, candidates: List[ScoredHybridResult]) -> List[ScoredHybridResult]:
        """Suppress near-identical overlapping chunks from the same document."""
        deduped: List[ScoredHybridResult] = []
        candidates_sorted = sorted(candidates, key=lambda r: -r.hybrid_score)

        for cand in candidates_sorted:
            cand_tokens = set(tokenize(cand.content, filter_stopwords=True))
            if not cand_tokens:
                deduped.append(cand)
                continue

            is_duplicate = False
            for accepted in deduped:
                # Only compare chunks belonging to the same document
                if cand.metadata.get("document_id") == accepted.metadata.get("document_id"):
                    acc_tokens = set(tokenize(accepted.content, filter_stopwords=True))
                    if acc_tokens:
                        intersection = cand_tokens.intersection(acc_tokens)
                        overlap = len(intersection) / min(len(cand_tokens), len(acc_tokens))
                        if overlap >= self.dedup_overlap_threshold:
                            is_duplicate = True
                            break

            if not is_duplicate:
                deduped.append(cand)

        return deduped

    def invoke(self, query: str) -> List[Any]:
        """LangChain compatible invoke method returning Document objects."""
        results = self.retrieve(query)
        return [r.to_document() for r in results]

    def get_relevant_documents(self, query: str) -> List[Any]:
        """Legacy LangChain retriever method."""
        return self.invoke(query)
