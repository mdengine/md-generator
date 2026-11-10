"""Prebuilt StateGraph workflow constructor with always-active conditional routing and checkpointer support."""

import math
from typing import Any, Optional
from md_generator.adapters.langchain.context import PromptContextBuilder
from md_generator.adapters.langchain.retriever import MDVectorStoreRetriever
from md_generator.adapters.langgraph.exceptions import LangGraphDependencyError
from md_generator.adapters.langgraph.nodes import (
    create_context_builder_node,
    create_fallback_node,
    create_retrieval_node,
    create_router_node,
)
from md_generator.adapters.langgraph.state import MDEngineGraphState

__all__ = ["build_rag_workflow"]

try:
    from langgraph.graph import END, StateGraph
except ImportError:
    StateGraph = None
    END = None


def build_rag_workflow(
    retriever: MDVectorStoreRetriever,
    builder: PromptContextBuilder,
    min_score: float = 0.0,
    checkpointer: Optional[Any] = None,
) -> Any:
    r"""Builds and compiles a canonical LangGraph RAG workflow with always-active routing.
    
    Graph Topology:
        START -> retrieve -> [router] -> (max_score >= min_score and docs > 0) -> context  -> END
                                       \-> (docs == 0 or max_score < min_score)  -> fallback -> END
    """
    if StateGraph is None:
        raise LangGraphDependencyError(
            "langgraph is required to build StateGraph workflows. Install via 'pip install langgraph'."
        )

    # Validate threshold strictly at construction time (P2A-R05)
    if isinstance(min_score, bool):
        raise ValueError("min_score cannot be a boolean.")
    if not isinstance(min_score, (int, float)):
        raise ValueError(f"min_score must be a numeric float or int, got {type(min_score).__name__}.")
    min_score_val = float(min_score)
    if math.isnan(min_score_val) or math.isinf(min_score_val):
        raise ValueError("min_score cannot be NaN or Infinite.")
    if not (0.0 <= min_score_val <= 1.0):
        raise ValueError(f"min_score must be within [0.0, 1.0], got {min_score_val}.")

    trusted_tenant = retriever.tenant_id

    workflow = StateGraph(MDEngineGraphState)
    
    # Register functional nodes with bound trusted tenant
    workflow.add_node("retrieve", create_retrieval_node(retriever, trusted_tenant=trusted_tenant))
    workflow.add_node("context", create_context_builder_node(builder, trusted_tenant=trusted_tenant))
    workflow.add_node("fallback", create_fallback_node(trusted_tenant=trusted_tenant))
    
    # Set entry point
    workflow.set_entry_point("retrieve")
    
    # ALWAYS register conditional routing (P2A-02)
    workflow.add_conditional_edges(
        "retrieve",
        create_router_node(
            min_score=min_score_val,
            trusted_tenant=trusted_tenant,
            has_docs_route="context",
            fallback_route="fallback",
        ),
        {"context": "context", "fallback": "fallback"},
    )
        
    workflow.add_edge("context", END)
    workflow.add_edge("fallback", END)
    
    return workflow.compile(checkpointer=checkpointer)
