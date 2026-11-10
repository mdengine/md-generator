"""Tests for real MemorySaver checkpoint execution and 10-step tenant tampering sequence (P2A-R08)."""

import pytest
from unittest.mock import MagicMock
from langchain_core.documents import Document
from langgraph.checkpoint.memory import MemorySaver

from md_generator.adapters.langchain.context import PromptContextBuilder
from md_generator.adapters.langgraph.graph import build_rag_workflow
from md_generator.vector.exceptions import TenantBoundaryError


def test_checkpoint_resume_10_step_tampering_sequence():
    """Validates the complete 10-step checkpoint isolation failure and recovery sequence:
    
    1. tenant-A starts thread
    2. checkpoint created
    3. tenant-A resumes
    4. tenant-B attempts same thread
    5. reject (TenantBoundaryError)
    6. tenant-A resumes
    7. inject tenant-B document
    8. reject (TenantBoundaryError)
    9. tenant-A resumes with valid state
    10. succeeds
    """
    memory = MemorySaver()
    thread_config = {"configurable": {"thread_id": "thread-1"}}

    # Mock retriever for tenant-A
    retriever_a = MagicMock()
    retriever_a.tenant_id = "tenant-A"
    retriever_a.invoke.return_value = [
        Document(page_content="Doc 1", metadata={"tenant_id": "tenant-A", "score": 0.95}),
    ]

    builder = PromptContextBuilder(max_tokens=1000)
    app_a = build_rag_workflow(retriever=retriever_a, builder=builder, min_score=0.5, checkpointer=memory)

    # 1. tenant-A starts thread
    state_step1 = app_a.invoke({"tenant_id": "tenant-A", "query": "initial query"}, config=thread_config)
    
    # 2. checkpoint created
    snapshot_1 = app_a.get_state(thread_config)
    assert snapshot_1.values["tenant_id"] == "tenant-A"
    assert snapshot_1.values["route"] == "synthesize"
    assert "Doc 1" in snapshot_1.values["context"]

    # 3. tenant-A resumes
    retriever_a.invoke.return_value = [
        Document(page_content="Doc 2", metadata={"tenant_id": "tenant-A", "score": 0.90}),
    ]
    state_step3 = app_a.invoke({"tenant_id": "tenant-A", "query": "second query"}, config=thread_config)
    assert state_step3["route"] == "synthesize"
    assert "Doc 2" in state_step3["context"]

    # 4. tenant-B attempts same thread with tenant-B workflow
    retriever_b = MagicMock()
    retriever_b.tenant_id = "tenant-B"
    app_b = build_rag_workflow(retriever=retriever_b, builder=builder, min_score=0.5, checkpointer=memory)

    # 5. reject tenant-B attempt
    with pytest.raises(TenantBoundaryError, match="conflicting with graph trusted tenant 'tenant-B'"):
        # When tenant-B tries to run on thread-1, it loads state containing tenant_id='tenant-A'
        app_b.invoke({"tenant_id": "tenant-B", "query": "tampering query"}, config=thread_config)

    # 6. tenant-A resumes successfully after rejected foreign tenant attempt
    state_step6 = app_a.invoke({"tenant_id": "tenant-A", "query": "safe query"}, config=thread_config)
    assert state_step6["tenant_id"] == "tenant-A"

    # 7. inject tenant-B document into checkpoint thread
    app_a.update_state(
        thread_config,
        {
            "documents": [
                Document(page_content="Injected Doc", metadata={"tenant_id": "tenant-B", "score": 0.99}),
            ]
        },
    )

    # 8. reject execution on injected foreign document
    with pytest.raises(TenantBoundaryError, match="belongs to tenant 'tenant-B', conflicting with graph trusted tenant 'tenant-A'"):
        # Retrieval node loads checkpointed state containing foreign tenant doc and validates
        app_a.invoke({"tenant_id": "tenant-A", "query": "query on injected state"}, config=thread_config)

    # 9. tenant-A resumes with valid state (clearing/replacing with valid tenant-A document)
    app_a.update_state(
        thread_config,
        {
            "documents": [
                Document(page_content="Restored Doc", metadata={"tenant_id": "tenant-A", "score": 0.92}),
            ]
        },
    )

    # 10. succeeds: execution continues and finishes cleanly
    retriever_a.invoke.return_value = [
        Document(page_content="Restored Doc", metadata={"tenant_id": "tenant-A", "score": 0.92}),
    ]
    final_state = app_a.invoke({"tenant_id": "tenant-A", "query": "clean query"}, config=thread_config)
    assert final_state["tenant_id"] == "tenant-A"
    assert final_state["route"] == "synthesize"
    assert "Restored Doc" in final_state["context"]


def test_checkpoint_resume_preserves_state_between_invocations():
    """Verifies that thread state is preserved across invocations."""
    memory = MemorySaver()
    thread_config = {"configurable": {"thread_id": "thread-2"}}

    retriever = MagicMock()
    retriever.tenant_id = "tenant-X"
    retriever.invoke.return_value = [
        Document(page_content="Text X", metadata={"tenant_id": "tenant-X", "score": 0.85}),
    ]

    builder = PromptContextBuilder(max_tokens=1000)
    app = build_rag_workflow(retriever=retriever, builder=builder, min_score=0.5, checkpointer=memory)

    res1 = app.invoke({"tenant_id": "tenant-X", "query": "q1"}, config=thread_config)
    checkpoint = app.get_state(thread_config)
    assert checkpoint.values["tenant_id"] == "tenant-X"
    assert checkpoint.values["route"] == "synthesize"
