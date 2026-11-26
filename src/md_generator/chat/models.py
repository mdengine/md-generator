from __future__ import annotations

"""Domain Models & Data Contracts for Multi-turn Conversational Chat Engine.

Phase 2D/Prompt 06 Implementation:
- Structured ChatResponse independent of any UI/web framework.
- Multi-turn ChatSession, ChatMessage, and ChatTurnRequest models.
- ExecutionMode selection (Extractive by default, Local LLM, Enterprise Intelligence).
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
import time
from typing import Any, Dict, List, Optional, Set

from md_generator.context.citation import Citation
from md_generator.context.validator import EvidenceValidationResult


class ExecutionMode(str, Enum):
    """Execution strategy for generating responses."""
    EXTRACTIVE = "extractive"    # Default: pure Python, zero-AI, 100% offline
    LOCAL_LLM = "local_llm"      # Local inference via Ollama / OpenAI-compatible endpoint
    ENTERPRISE = "enterprise"    # Enterprise provider via secure adapters


class MessageRole(str, Enum):
    """Role associated with a chat message."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """Individual message within a conversational turn."""
    message_id: str
    turn_id: str
    role: MessageRole
    content: str
    timestamp: float = field(default_factory=time.time)
    citations: List[Citation] = field(default_factory=list)
    evidence_references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "turn_id": self.turn_id,
            "role": self.role.value if isinstance(self.role, MessageRole) else str(self.role),
            "content": self.content,
            "timestamp": self.timestamp,
            "citations": [c.to_dict() for c in self.citations],
            "evidence_references": list(self.evidence_references),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChatMessage:
        citations = [Citation(**c) if not isinstance(c, Citation) else c for c in data.get("citations", [])]
        role = MessageRole(data.get("role", "user"))
        return cls(
            message_id=data["message_id"],
            turn_id=data["turn_id"],
            role=role,
            content=data["content"],
            timestamp=float(data.get("timestamp", time.time())),
            citations=citations,
            evidence_references=list(data.get("evidence_references", [])),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class ChatSession:
    """Multi-turn conversation session tracking history, entities, and context."""
    session_id: str
    conversation_id: str
    tenant_id: str
    user_id: str = "default_user"
    title: str = "New Conversation"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    messages: List[ChatMessage] = field(default_factory=list)
    active_topic: str = ""
    active_document_ids: Set[str] = field(default_factory=set)
    tracked_entities: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [m.to_dict() for m in self.messages],
            "active_topic": self.active_topic,
            "active_document_ids": sorted(list(self.active_document_ids)),
            "tracked_entities": dict(self.tracked_entities),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChatSession:
        msgs = [ChatMessage.from_dict(m) for m in data.get("messages", [])]
        return cls(
            session_id=data["session_id"],
            conversation_id=data["conversation_id"],
            tenant_id=data["tenant_id"],
            user_id=data.get("user_id", "default_user"),
            title=data.get("title", "New Conversation"),
            created_at=float(data.get("created_at", time.time())),
            updated_at=float(data.get("updated_at", time.time())),
            messages=msgs,
            active_topic=data.get("active_topic", ""),
            active_document_ids=set(data.get("active_document_ids", [])),
            tracked_entities=dict(data.get("tracked_entities", {})),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class ChatTurnRequest:
    """Request payload for processing a conversational chat turn."""
    query: str
    conversation_id: Optional[str] = None
    session_id: Optional[str] = None
    tenant_id: str = "default"
    user_id: str = "default_user"
    mode: ExecutionMode = ExecutionMode.EXTRACTIVE
    document_ids: Optional[Set[str]] = None
    top_k: int = 5
    max_tokens: int = 4000
    system_instructions: Optional[str] = None
    generation_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatResponse:
    """Canonical framework-neutral chat response object."""
    conversation_id: str
    session_id: str
    turn_id: str
    query: str
    answer: str
    execution_mode: ExecutionMode
    citations: List[Citation] = field(default_factory=list)
    evidence_references: List[str] = field(default_factory=list)
    retrieved_chunks: List[Any] = field(default_factory=list)
    token_usage: Dict[str, int] = field(default_factory=dict)
    context_summary: str = ""
    validation_status: Optional[EvidenceValidationResult] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        val_status_dict = None
        if self.validation_status:
            val_status_dict = {
                "is_valid": self.validation_status.is_valid,
                "coverage_ratio": self.validation_status.coverage_ratio,
                "hallucinated_citations": list(self.validation_status.hallucinated_citations),
                "conflicts_count": len(self.validation_status.conflicts),
                "notes": list(self.validation_status.validation_notes),
            }

        return {
            "conversation_id": self.conversation_id,
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "query": self.query,
            "answer": self.answer,
            "execution_mode": self.execution_mode.value if isinstance(self.execution_mode, ExecutionMode) else str(self.execution_mode),
            "citations": [c.to_dict() for c in self.citations],
            "evidence_references": list(self.evidence_references),
            "token_usage": dict(self.token_usage),
            "context_summary": self.context_summary,
            "validation_status": val_status_dict,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "timestamp": self.timestamp,
        }
