"""LangGraph adapter package for md_generator.

Provides functional workflow nodes, strict tenant isolation, and prebuilt RAG
StateGraph workflows for LangGraph multi-agent systems.
"""

from md_generator.adapters.langgraph.exceptions import (
    GraphRoutingError,
    GraphStateValidationError,
    LangGraphAdapterError,
    LangGraphDependencyError,
)
from md_generator.adapters.langgraph.graph import build_rag_workflow
from md_generator.adapters.langgraph.nodes import (
    create_context_builder_node,
    create_fallback_node,
    create_retrieval_node,
    create_router_node,
    to_langchain_document,
)
from md_generator.adapters.langgraph.state import (
    ALLOWED_ROUTES,
    DocumentStateDTO,
    MDEngineGraphState,
    validate_graph_state,
    validate_serializable_value,
)

__all__ = [
    "ALLOWED_ROUTES",
    "DocumentStateDTO",
    "GraphRoutingError",
    "GraphStateValidationError",
    "LangGraphAdapterError",
    "LangGraphDependencyError",
    "MDEngineGraphState",
    "build_rag_workflow",
    "create_context_builder_node",
    "create_fallback_node",
    "create_retrieval_node",
    "create_router_node",
    "to_langchain_document",
    "validate_graph_state",
    "validate_serializable_value",
]
