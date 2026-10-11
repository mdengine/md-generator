"""MDSearchTool adapter for CrewAI agents with bound tenant isolation and score filtering."""

import math
from typing import Any, Optional, Type
from pydantic import BaseModel, ConfigDict, PrivateAttr

from md_generator.adapters.crewai.exceptions import (
    CrewAIDependencyError,
    CrewAIToolExecutionError,
    TenantBoundaryError,
)
from md_generator.adapters.crewai.schema import MDSearchInput
from md_generator.adapters.langchain.context import PromptContextBuilder
from md_generator.adapters.langchain.retriever import MDVectorStoreRetriever

__all__ = ["MDSearchTool"]

# Dynamic dependency detection (P2B-V03)
CrewAIBaseTool: Optional[Type[Any]] = None
try:
    from crewai.tools import BaseTool as _DetectedBaseTool
    CrewAIBaseTool = _DetectedBaseTool
except ImportError as err:
    if err.name in ("crewai", "crewai.tools", None):
        try:
            from crewai_tools import BaseTool as _DetectedToolsBaseTool
            CrewAIBaseTool = _DetectedToolsBaseTool
        except ImportError as err_tools:
            if err_tools.name in ("crewai_tools", None):
                CrewAIBaseTool = None
            else:
                raise CrewAIDependencyError(f"Broken crewai_tools installation: {err_tools}") from err_tools
    else:
        raise CrewAIDependencyError(f"Broken crewai installation: {err}") from err


class _FallbackBaseTool(BaseModel):
    """Pydantic v2 fallback providing the identical public compatibility surface when CrewAI is absent."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "enterprise_knowledge_search"
    description: str = (
        "Search enterprise markdown and code documentation with token-budgeted prompt context and source citations."
    )
    args_schema: Type[BaseModel] = MDSearchInput

    def run(self, *args: Any, **kwargs: Any) -> str:
        return self._run(*args, **kwargs)

    def _run(self, *args: Any, **kwargs: Any) -> str:
        raise NotImplementedError


_ToolBase = CrewAIBaseTool if CrewAIBaseTool is not None else _FallbackBaseTool


class MDSearchTool(_ToolBase):
    """CrewAI search tool adapter bridging mdengine retrieval to multi-agent ecosystems.
    
    Invariants:
        1. Mandatory Bound Tenant Isolation (C1): Bound to a single immutable tenant_id at construction.
        2. Input Schema Contract (C2): Pydantic v2 strict input schema with extra='forbid'.
        3. Document Score Contract (C3): Scores validated in [0.0, 1.0] and filtered by min_score.
        4. Deterministic Output (C4): Structured PromptContextBuilder output; informative string on 0 results.
        5. Zero In-Place Mutation: Never alters retriever, vector store, or document states.
    """
    name: str = "enterprise_knowledge_search"
    description: str = (
        "Search enterprise markdown and code documentation with token-budgeted prompt context and source citations."
    )
    args_schema: Type[BaseModel] = MDSearchInput

    _retriever: Any = PrivateAttr()
    _tenant_id: str = PrivateAttr()
    _min_score: float = PrivateAttr()
    _builder: PromptContextBuilder = PrivateAttr()
    _is_frozen: bool = PrivateAttr(default=False)

    def __init__(
        self,
        retriever: MDVectorStoreRetriever,
        tenant_id: str,
        min_score: float = 0.0,
        builder: Optional[PromptContextBuilder] = None,
        **kwargs: Any,
    ) -> None:
        # 1. Mandatory construction-time tenant validation (P2B-V04)
        if tenant_id is None or not isinstance(tenant_id, str) or not tenant_id.strip():
            raise TenantBoundaryError("MDSearchTool requires a mandatory non-empty string 'tenant_id'.")
        clean_tenant = tenant_id.strip()

        if not hasattr(retriever, "tenant_id"):
            raise TenantBoundaryError("retriever must provide a valid 'tenant_id' attribute.")
        retriever_tenant = getattr(retriever, "tenant_id")
        if not retriever_tenant or clean_tenant != retriever_tenant.strip():
            raise TenantBoundaryError(
                f"Tool tenant_id '{clean_tenant}' conflicts with retriever tenant_id '{retriever_tenant}'."
            )

        # 2. Strict threshold validation (P2B-V05)
        if isinstance(min_score, bool):
            raise ValueError("min_score cannot be a boolean.")
        if not isinstance(min_score, (int, float)):
            raise ValueError(f"min_score must be a numeric float or int, got {type(min_score).__name__}.")
        min_score_val = float(min_score)
        if math.isnan(min_score_val) or math.isinf(min_score_val):
            raise ValueError("min_score cannot be NaN or Infinite.")
        if not (0.0 <= min_score_val <= 1.0):
            raise ValueError(f"min_score must be between 0.0 and 1.0, got {min_score_val}.")

        # 3. Builder initialization
        if builder is None:
            builder = PromptContextBuilder()

        super().__init__(**kwargs)
        self._retriever = retriever
        self._tenant_id = clean_tenant
        self._min_score = min_score_val
        self._builder = builder
        self._is_frozen = True

    @property
    def tenant_id(self) -> str:
        """Immutable trusted tenant identifier bound at construction."""
        return self._tenant_id

    @property
    def min_score(self) -> float:
        """Minimum relevance threshold for document inclusion."""
        return self._min_score

    @property
    def retriever(self) -> Any:
        """Bound vector store retriever."""
        return self._retriever

    @property
    def builder(self) -> PromptContextBuilder:
        """Bound context builder."""
        return self._builder

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_is_frozen", False) and name in ("tenant_id", "_tenant_id"):
            raise AttributeError("tenant_id is immutable and cannot be reassigned.")
        super().__setattr__(name, value)

    def _run(self, *args: Any, **kwargs: Any) -> str:
        """Executes tenant-isolated retrieval, document validation, score filtering, and context synthesis."""
        # 1. Parse arguments and enforce Pydantic v2 schema validation (P2B-V01, P2B-V06)
        if args:
            if len(args) == 1 and isinstance(args[0], str) and "query" not in kwargs:
                kwargs["query"] = args[0]
            else:
                raise ValueError("Positional argument must be a single query string.")

        validated = MDSearchInput.model_validate(kwargs)
        query_str = validated.query

        # 2. Invoke retriever
        raw_docs = self._retriever.invoke(query_str) or []

        # 3. Deep document tenant ownership validation (P2B-V04)
        for i, doc in enumerate(raw_docs):
            meta = doc.metadata if hasattr(doc, "metadata") else (doc.get("metadata", {}) if isinstance(doc, dict) else {})
            doc_tenant = meta.get("tenant_id")
            if doc_tenant is None or not isinstance(doc_tenant, str) or not doc_tenant.strip():
                raise TenantBoundaryError(
                    f"Retrieved document at index {i} missing mandatory non-empty 'tenant_id' in metadata."
                )
            if doc_tenant.strip() != self._tenant_id:
                raise TenantBoundaryError(
                    f"Retrieved document at index {i} belongs to tenant '{doc_tenant.strip()}', "
                    f"conflicting with bound tool tenant '{self._tenant_id}'."
                )

        # 4. Document score validation & threshold filtering (P2B-V05)
        qualifying_docs = []
        for i, doc in enumerate(raw_docs):
            meta = doc.metadata if hasattr(doc, "metadata") else (doc.get("metadata", {}) if isinstance(doc, dict) else {})
            if "score" not in meta:
                raise CrewAIToolExecutionError(f"Retrieved document at index {i} missing mandatory 'score' in metadata.")
            raw_score = meta["score"]
            if raw_score is None:
                raise CrewAIToolExecutionError(f"Retrieved document at index {i} has None 'score'.")
            if isinstance(raw_score, bool):
                raise CrewAIToolExecutionError(f"Retrieved document at index {i} has boolean 'score'.")
            if not isinstance(raw_score, (int, float)):
                raise CrewAIToolExecutionError(
                    f"Retrieved document at index {i} has non-numeric score of type '{type(raw_score).__name__}'."
                )
            if math.isnan(raw_score) or math.isinf(raw_score):
                raise CrewAIToolExecutionError(f"Retrieved document at index {i} has non-finite score: {raw_score}.")
            if not (0.0 <= raw_score <= 1.0):
                raise CrewAIToolExecutionError(f"Retrieved document at index {i} score {raw_score} is outside [0.0, 1.0].")

            if float(raw_score) >= self._min_score:
                qualifying_docs.append(doc)

        # 5. Empty results contract (P2B-V06, P2B-V07)
        if not qualifying_docs:
            return f"No relevant documents found for query: '{query_str}'."

        # 6. Context synthesis via PromptContextBuilder
        return self._builder.build_context(qualifying_docs)

    def run(self, *args: Any, **kwargs: Any) -> str:
        """Public execution entry point conforming to CrewAI tool invocation protocol."""
        return self._run(*args, **kwargs)
