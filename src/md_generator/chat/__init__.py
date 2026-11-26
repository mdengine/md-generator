from __future__ import annotations

"""Multi-turn Conversational Chat Engine Package.

Phase 2D/Prompt 06 Implementation:
- Framework-neutral chat engine orchestration.
- Execution modes: Extractive (default), Local LLM, Enterprise Intelligence.
- Multi-turn conversation sessions, short-term memory, reference resolution, and history pruning.
- Evidence-grounded answers with verifiable citations.
"""

from md_generator.chat.models import (
    ChatMessage,
    ChatResponse,
    ChatSession,
    ChatTurnRequest,
    ExecutionMode,
    MessageRole,
)
from md_generator.chat.session import (
    BaseSessionStore,
    InMemorySessionStore,
    FileSessionStore,
)
from md_generator.chat.memory import (
    ConversationMemory,
)
from md_generator.chat.pruning import (
    ConversationPruner,
)
from md_generator.chat.providers.base import (
    BaseChatProvider,
)
from md_generator.chat.providers.extractive import (
    ExtractiveChatProvider,
    INSUFFICIENT_EVIDENCE_RESPONSE,
)
from md_generator.chat.providers.local_llm import (
    LocalLLMChatProvider,
    LocalLLMUnavailableError,
)
from md_generator.chat.providers.enterprise import (
    EnterpriseChatProvider,
    EnterpriseProviderError,
)
from md_generator.chat.manager import (
    ChatManager,
)

__all__ = [
    # Models
    "ChatMessage",
    "ChatResponse",
    "ChatSession",
    "ChatTurnRequest",
    "ExecutionMode",
    "MessageRole",
    # Sessions
    "BaseSessionStore",
    "InMemorySessionStore",
    "FileSessionStore",
    # Memory & Pruning
    "ConversationMemory",
    "ConversationPruner",
    # Providers
    "BaseChatProvider",
    "ExtractiveChatProvider",
    "INSUFFICIENT_EVIDENCE_RESPONSE",
    "LocalLLMChatProvider",
    "LocalLLMUnavailableError",
    "EnterpriseChatProvider",
    "EnterpriseProviderError",
    # Manager
    "ChatManager",
]
