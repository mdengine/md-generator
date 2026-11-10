from __future__ import annotations

"""Hybrid GraphRAG Retriever: Vector Bridge, Topological Graph Scoring & Fusion.

Phase 2C Implementation: Connects Phase 1C vector retrieval to graph expansion,
reconstructs deterministic GraphPath instances, computes topological graph proximity scores,
applies normalized RRF (absent-list omission math) or linear combination fusion,
and enforces candidate-set membership provenance (VECTOR_ONLY, GRAPH_ONLY, HYBRID).
"""

from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

from md_generator.graph.exceptions import GraphQueryError, TenantBoundaryError
from md_generator.graph.model import (
    EntityNode,
    GraphPath,
    KnowledgeGraph,
    RelationEdge,
    _validate_tenant_id,
    canonical_chunk_node_id,
)
from md_generator.graph.protocol import GraphStore


@dataclass
class ScoredHybridResult:
    """Unified hybrid retrieval candidate result."""
    chunk_id: str
    content: str
    tenant_id: str
    vector_score: float
    graph_score: float
    hybrid_score: float
    provenance: Literal["VECTOR_ONLY", "GRAPH_ONLY", "HYBRID"]
    metadata: Dict[str, Any] = field(default_factory=dict)
    graph_paths: List[GraphPath] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "tenant_id": self.tenant_id,
            "vector_score": self.vector_score,
            "graph_score": self.graph_score,
            "hybrid_score": self.hybrid_score,
            "provenance": self.provenance,
            "metadata": dict(self.metadata),
            "graph_paths": [p.to_dict() for p in self.graph_paths],
        }

    def to_document(self) -> Any:
        """Converts result to a LangChain Document compatible object."""
        try:
            from langchain_core.documents import Document
        except ImportError:
            # Fallback document dataclass
            @dataclass
            class Document:  # type: ignore[no-redef]
                page_content: str
                metadata: Dict[str, Any]

        doc_meta = dict(self.metadata)
        doc_meta.update({
            "chunk_id": self.chunk_id,
            "tenant_id": self.tenant_id,
            "score": self.hybrid_score,
            "vector_score": self.vector_score,
            "graph_score": self.graph_score,
            "provenance": self.provenance,
            "graph_paths": [p.to_dict() for p in self.graph_paths],
        })
        return Document(page_content=self.content, metadata=doc_meta)


class HybridGraphRAGRetriever:
    """Retrieves and fusions vector similarity results with graph expansion."""

    def __init__(
        self,
        vector_retriever: Any,
        graph_store: GraphStore,
        tenant_id: str,
        top_k: int = 10,
        max_depth: int = 2,
        fusion_mode: Literal["rrf", "linear"] = "rrf",
        alpha: float = 0.7,
        rrf_k: int = 60,
        weight_vector: float = 1.0,
        weight_graph: float = 1.0,
    ) -> None:
        self.clean_tenant = _validate_tenant_id(tenant_id, "HybridGraphRAGRetriever.tenant_id")
        self.tenant_id = self.clean_tenant

        if hasattr(vector_retriever, "tenant_id"):
            v_tenant = getattr(vector_retriever, "tenant_id")
            if v_tenant != self.clean_tenant:
                raise TenantBoundaryError(
                    f"vector_retriever tenant_id '{v_tenant}' does not match retriever tenant_id '{self.clean_tenant}'."
                )

        if not isinstance(top_k, int) or top_k <= 0:
            raise ValueError(f"top_k must be an integer > 0. Got: {top_k!r}")
        if not isinstance(max_depth, int) or max_depth < 0:
            raise ValueError(f"max_depth must be an integer >= 0. Got: {max_depth!r}")
        if fusion_mode not in ("rrf", "linear"):
            raise ValueError(f"fusion_mode must be 'rrf' or 'linear'. Got: {fusion_mode!r}")

        if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not (0.0 <= alpha <= 1.0):
            raise ValueError(f"alpha must be a float in [0.0, 1.0]. Got: {alpha!r}")

        if not isinstance(rrf_k, int) or rrf_k <= 0:
            raise ValueError(f"rrf_k must be an integer > 0. Got: {rrf_k!r}")
        if isinstance(weight_vector, bool) or not isinstance(weight_vector, (int, float)) or weight_vector < 0.0:
            raise ValueError(f"weight_vector must be a float >= 0.0. Got: {weight_vector!r}")
        if isinstance(weight_graph, bool) or not isinstance(weight_graph, (int, float)) or weight_graph < 0.0:
            raise ValueError(f"weight_graph must be a float >= 0.0. Got: {weight_graph!r}")
        if weight_vector + weight_graph <= 0.0:
            raise ValueError("weight_vector + weight_graph must be strictly > 0.0.")

        self.vector_retriever = vector_retriever
        self.graph_store = graph_store
        self.top_k = top_k
        self.max_depth = max_depth
        self.fusion_mode = fusion_mode
        self.alpha = float(alpha)
        self.rrf_k = rrf_k
        self.weight_vector = float(weight_vector)
        self.weight_graph = float(weight_graph)

    def retrieve(self, query: str) -> List[ScoredHybridResult]:
        """Performs end-to-end hybrid retrieval with graph expansion and fusion."""
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query string must be non-empty.")

        # 1. Vector Retrieval
        vector_docs: List[Any] = []
        if hasattr(self.vector_retriever, "invoke"):
            vector_docs = self.vector_retriever.invoke(query)
        elif hasattr(self.vector_retriever, "get_relevant_documents"):
            vector_docs = self.vector_retriever.get_relevant_documents(query)
        else:
            raise ValueError("vector_retriever must provide invoke() or get_relevant_documents() method.")

        # Map vector candidates: chunk_id -> (doc, vector_score)
        v_candidates: Dict[str, Tuple[Any, float]] = {}
        for rank_idx, doc in enumerate(vector_docs):
            meta = getattr(doc, "metadata", {}) or {}
            # Verify tenant
            doc_tenant = meta.get("tenant_id")
            if doc_tenant and doc_tenant != self.clean_tenant:
                raise TenantBoundaryError(
                    f"Retrieved document tenant_id '{doc_tenant}' conflicts with retriever tenant_id '{self.clean_tenant}'."
                )

            cid = meta.get("chunk_id") or getattr(doc, "id", None)
            if not cid:
                cid = f"vec_doc_{rank_idx}"

            raw_score = meta.get("score")
            score = 1.0 / (1.0 + rank_idx)  # Fallback monotonic score if none present
            if raw_score is not None and isinstance(raw_score, (int, float)) and not isinstance(raw_score, bool):
                score = max(0.0, min(1.0, float(raw_score)))

            v_candidates[cid] = (doc, score)

        # 2. Graph Expansion via canonical chunk_id bridge
        g_candidates: Dict[str, Tuple[float, List[GraphPath]]] = {}
        # Start node IDs
        seed_chunk_ids = list(v_candidates.keys())
        seed_node_map = {
            canonical_chunk_node_id(self.clean_tenant, cid): cid for cid in seed_chunk_ids
        }
        start_node_ids = list(seed_node_map.keys())

        if start_node_ids and self.max_depth >= 0:
            subgraph = self.graph_store.traverse(
                start_node_ids=start_node_ids,
                tenant_id=self.clean_tenant,
                max_depth=self.max_depth,
                direction="both",
                strategy="bfs",
            )
            # Reconstruct paths and compute topological scores
            g_candidates = self._reconstruct_paths_and_scores(
                subgraph=subgraph,
                seed_node_map=seed_node_map,
            )

        # 3. Union Candidate Universe & Determine Candidate-Set Membership Provenance
        universe_cids: Set[str] = set(v_candidates.keys()).union(set(g_candidates.keys()))

        ranked_results: List[ScoredHybridResult] = []

        # Build ranking lists for RRF (1-based ranks) with deterministic tie-breaking on (-score, cid)
        sorted_v = sorted(v_candidates.keys(), key=lambda cid: (-v_candidates[cid][1], cid))
        v_rank_map = {cid: rank + 1 for rank, cid in enumerate(sorted_v)}

        sorted_g = sorted(g_candidates.keys(), key=lambda cid: (-g_candidates[cid][0], cid))
        g_rank_map = {cid: rank + 1 for rank, cid in enumerate(sorted_g)}

        # Maximum possible RRF raw score for normalization
        rrf_max = (self.weight_vector / (self.rrf_k + 1)) + (self.weight_graph / (self.rrf_k + 1))

        for cid in universe_cids:
            in_v = cid in v_candidates
            in_g = cid in g_candidates

            if in_v and in_g:
                prov: Literal["VECTOR_ONLY", "GRAPH_ONLY", "HYBRID"] = "HYBRID"
            elif in_v:
                prov = "VECTOR_ONLY"
            else:
                prov = "GRAPH_ONLY"

            doc_obj = v_candidates[cid][0] if in_v else None
            content = getattr(doc_obj, "page_content", "") if doc_obj else f"[Graph Node: {cid}]"
            metadata = dict(getattr(doc_obj, "metadata", {})) if doc_obj else {"chunk_id": cid, "tenant_id": self.clean_tenant}

            s_v = v_candidates[cid][1] if in_v else 0.0
            s_g = g_candidates[cid][0] if in_g else 0.0
            paths = g_candidates[cid][1] if in_g else []

            # Compute hybrid score
            if self.fusion_mode == "linear":
                s_hybrid = (self.alpha * s_v) + ((1.0 - self.alpha) * s_g)
            else:
                # Normalized RRF with absent-list omission
                rrf_raw = 0.0
                if in_v:
                    rrf_raw += self.weight_vector / (self.rrf_k + v_rank_map[cid])
                if in_g:
                    rrf_raw += self.weight_graph / (self.rrf_k + g_rank_map[cid])
                s_hybrid = rrf_raw / rrf_max if rrf_max > 0.0 else 0.0

            # Strictly clip to [0.0, 1.0]
            s_hybrid = max(0.0, min(1.0, float(s_hybrid)))

            result = ScoredHybridResult(
                chunk_id=cid,
                content=content,
                tenant_id=self.clean_tenant,
                vector_score=s_v,
                graph_score=s_g,
                hybrid_score=s_hybrid,
                provenance=prov,
                metadata=metadata,
                graph_paths=paths,
            )
            ranked_results.append(result)

        # Deterministic sorting: (-hybrid_score, -vector_score, -graph_score, chunk_id)
        ranked_results.sort(
            key=lambda r: (-r.hybrid_score, -r.vector_score, -r.graph_score, r.chunk_id)
        )

        return ranked_results[: self.top_k]

    def invoke(self, query: str) -> List[Any]:
        """LangChain standard invoke method returning List[Document]."""
        results = self.retrieve(query)
        return [r.to_document() for r in results]

    def get_relevant_documents(self, query: str) -> List[Any]:
        """LangChain backward-compatible retriever API."""
        return self.invoke(query)

    def _reconstruct_paths_and_scores(
        self,
        subgraph: KnowledgeGraph,
        seed_node_map: Dict[str, str],
    ) -> Dict[str, Tuple[float, List[GraphPath]]]:
        """Reconstructs shortest/deterministic GraphPath instances and topological scores."""
        # seed_node_map: canonical_node_id -> seed_chunk_id
        g_candidates: Dict[str, Tuple[float, List[GraphPath]]] = {}

        # Adjacency for path search within subgraph
        adj: Dict[str, List[Tuple[str, str, float]]] = {}  # node -> list of (neighbor_id, edge_id, weight)
        for edge in subgraph.edges.values():
            adj.setdefault(edge.source_id, []).append((edge.target_id, edge.edge_id, edge.weight))
            adj.setdefault(edge.target_id, []).append((edge.source_id, edge.edge_id, edge.weight))

        # Sort adjacency deterministically
        for u in adj:
            adj[u].sort(key=lambda t: (t[0], t[1]))

        # For each seed node, compute shortest BFS paths to all reachable nodes
        for seed_node_id, seed_chunk_id in seed_node_map.items():
            if seed_node_id not in subgraph.nodes:
                continue

            # BFS from seed_node_id
            from collections import deque
            queue: deque[Tuple[str, List[str], List[str], List[float]]] = deque([
                (seed_node_id, [seed_node_id], [], [])
            ])

            # Seed chunk node itself: depth 0, score 1.0
            seed_path = GraphPath(
                seed_chunk_id=seed_chunk_id,
                target_node_id=seed_node_id,
                node_ids=[seed_node_id],
                edge_ids=[],
                depth=0,
                score=1.0,
            )
            if seed_chunk_id in g_candidates:
                prev_score, prev_paths = g_candidates[seed_chunk_id]
                new_paths = prev_paths + [seed_path]
                new_paths.sort(key=lambda p: (-p.score, p.depth))
                g_candidates[seed_chunk_id] = (max(prev_score, 1.0), new_paths)
            else:
                g_candidates[seed_chunk_id] = (1.0, [seed_path])

            while queue:
                curr_node, node_path, edge_path, weight_path = queue.popleft()
                depth = len(edge_path)
                if depth >= self.max_depth:
                    continue

                for neighbor_id, edge_id, weight in adj.get(curr_node, []):
                    # Explore all valid acyclic simple paths up to max_depth
                    if neighbor_id not in node_path:
                        new_node_path = node_path + [neighbor_id]
                        new_edge_path = edge_path + [edge_id]
                        new_weight_path = weight_path + [weight]

                        path_len = len(new_edge_path)
                        min_weight = min(new_weight_path) if new_weight_path else 1.0
                        # Topological score formula: (1.0 / (1.0 + len(P))) * min(weight)
                        p_score = (1.0 / (1.0 + path_len)) * min_weight
                        p_score = max(0.0, min(1.0, float(p_score)))

                        path_obj = GraphPath(
                            seed_chunk_id=seed_chunk_id,
                            target_node_id=neighbor_id,
                            node_ids=new_node_path,
                            edge_ids=new_edge_path,
                            depth=path_len,
                            score=p_score,
                        )

                        # Determine candidate chunk_id:
                        # If neighbor is a chunk node: entity_id is chunk_id
                        # If neighbor is an entity node: maps back to its chunk_ids or node_id
                        target_entity = subgraph.nodes.get(neighbor_id)
                        candidate_cids = []
                        if target_entity and target_entity.entity_type == "chunk":
                            candidate_cids.append(target_entity.entity_id)
                        elif target_entity and target_entity.chunk_ids:
                            candidate_cids.extend(target_entity.chunk_ids)
                        else:
                            # Map to node_id as fallback candidate
                            candidate_cids.append(neighbor_id)

                        for target_cid in candidate_cids:
                            if target_cid in g_candidates:
                                prev_s, prev_p = g_candidates[target_cid]
                                new_paths = prev_p + [path_obj]
                                new_paths.sort(key=lambda p: (-p.score, p.depth))
                                g_candidates[target_cid] = (max(prev_s, p_score), new_paths)
                            else:
                                g_candidates[target_cid] = (p_score, [path_obj])

                        queue.append((neighbor_id, new_node_path, new_edge_path, new_weight_path))

        return g_candidates
