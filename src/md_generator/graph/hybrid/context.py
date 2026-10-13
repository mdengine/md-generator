from __future__ import annotations

"""Graph Context Adapter: Augmenting Prompt Context with Graph Paths & Citations.

Phase 2C Implementation: Augments retrieved chunks with topological graph traversal paths,
formats deterministic relationship citations, and feeds enriched documents into
the frozen Phase 1C PromptContextBuilder respecting token budget limits.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from md_generator.adapters.langchain.context import PromptContextBuilder
from md_generator.graph.hybrid.retriever import ScoredHybridResult
from md_generator.graph.model import GraphPath, KnowledgeGraph


@dataclass
class _AugmentedDocument:
    """Internal lightweight document structure compatible with PromptContextBuilder."""
    page_content: str
    metadata: Dict[str, Any]


class GraphContextAdapter:
    """Adapts hybrid GraphRAG retrieval results for prompt synthesis."""

    def __init__(
        self,
        context_builder: Optional[PromptContextBuilder] = None,
        include_graph_paths: bool = True,
        max_paths_per_chunk: int = 5,
    ) -> None:
        self.context_builder = context_builder or PromptContextBuilder()
        self.include_graph_paths = include_graph_paths
        self.max_paths_per_chunk = max_paths_per_chunk

    def format_graph_paths(
        self,
        paths: List[GraphPath],
        subgraph: Optional[KnowledgeGraph] = None,
    ) -> str:
        """Formats graph traversal paths into human-readable deterministic markdown lines."""
        if not paths:
            return ""

        formatted_lines: List[str] = []
        # Sort paths deterministically by (-score, depth, target_node_id)
        sorted_paths = sorted(paths, key=lambda p: (-p.score, p.depth, p.target_node_id))[: self.max_paths_per_chunk]

        for p in sorted_paths:
            if not p.node_ids or len(p.node_ids) <= 1:
                continue

            node_labels: List[str] = []
            for nid in p.node_ids:
                if subgraph and nid in subgraph.nodes:
                    node_obj = subgraph.nodes[nid]
                    node_labels.append(f"{node_obj.name} ({node_obj.entity_type})")
                else:
                    # Clean identifier representation
                    short_id = nid.split(":")[-1] if ":" in nid else nid
                    node_labels.append(short_id)

            path_str = " -> ".join(node_labels)
            formatted_lines.append(
                f"[Graph Path (depth {p.depth}, score {p.score:.2f}): {path_str}]"
            )

        return "\n".join(formatted_lines)

    def augment_result(
        self,
        result: Union[ScoredHybridResult, Any],
        subgraph: Optional[KnowledgeGraph] = None,
    ) -> Any:
        """Augments a single hybrid result with its graph traversal context."""
        if isinstance(result, ScoredHybridResult):
            content = result.content
            meta = dict(result.metadata)
            meta.update({
                "chunk_id": result.chunk_id,
                "tenant_id": result.tenant_id,
                "score": result.hybrid_score,
                "vector_score": result.vector_score,
                "graph_score": result.graph_score,
                "provenance": result.provenance,
                "graph_paths": [p.to_dict() for p in result.graph_paths],
            })
            paths = result.graph_paths
        else:
            # Generic Document object
            content = getattr(result, "page_content", "") or ""
            meta = dict(getattr(result, "metadata", {}) or {})
            raw_paths = meta.get("graph_paths", [])
            paths = []
            for rp in raw_paths:
                if isinstance(rp, dict):
                    paths.append(GraphPath(
                        seed_chunk_id=rp.get("seed_chunk_id", ""),
                        target_node_id=rp.get("target_node_id", ""),
                        node_ids=list(rp.get("node_ids", [])),
                        edge_ids=list(rp.get("edge_ids", [])),
                        depth=int(rp.get("depth", 0)),
                        score=float(rp.get("score", 0.0)),
                    ))

        if self.include_graph_paths and paths:
            paths_text = self.format_graph_paths(paths, subgraph=subgraph)
            if paths_text:
                content = f"{content}\n\n--- Graph Relationships ---\n{paths_text}"

        return _AugmentedDocument(page_content=content, metadata=meta)

    def augment_documents(
        self,
        results: List[Union[ScoredHybridResult, Any]],
        subgraph: Optional[KnowledgeGraph] = None,
    ) -> List[Any]:
        """Augments a collection of hybrid retrieval results with graph paths."""
        return [self.augment_result(r, subgraph=subgraph) for r in results]

    def build_context(
        self,
        results: List[Union[ScoredHybridResult, Any]],
        subgraph: Optional[KnowledgeGraph] = None,
    ) -> str:
        """Augments results and synthesizes deterministic token-bounded prompt context."""
        augmented_docs = self.augment_documents(results, subgraph=subgraph)
        return self.context_builder.build_context(augmented_docs)
