from __future__ import annotations

"""ChatManager: Multi-turn Conversational Orchestration Engine.

Phase 2D/Prompt 06 Implementation:
- Connects EnterpriseHybridRetriever, ContextManager, EvidenceValidator, and ConversationMemory.
- Orchestrates three execution modes: Extractive (default), Local LLM, and Enterprise Intelligence.
- Enforces multi-tenant and user permission isolation.
- Defends against prompt injection and coreference ambiguity across multi-turn sessions.
- Produces structured, UI-independent ChatResponse contracts.
"""

from collections import defaultdict
import threading
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from md_generator.chat.models import (
    ChatMessage,
    ChatResponse,
    ChatSession,
    ChatTurnRequest,
    ExecutionMode,
    MessageRole,
)
from md_generator.chat.memory import ConversationMemory
from md_generator.chat.pruning import ConversationPruner
from md_generator.chat.providers.base import BaseChatProvider
from md_generator.chat.providers.extractive import ExtractiveChatProvider
from md_generator.chat.providers.local_llm import LocalLLMChatProvider, LocalLLMUnavailableError
from md_generator.chat.providers.enterprise import EnterpriseChatProvider, EnterpriseProviderError
from md_generator.chat.session import BaseSessionStore, InMemorySessionStore
from md_generator.context.manager import ContextManager, sanitize_untrusted_text
from md_generator.graph.model import _validate_tenant_id
from md_generator.graph.exceptions import TenantBoundaryError
from md_generator.retrieval.hybrid_retriever import EnterpriseHybridRetriever, HybridSearchFilter


class ChatManager:
    """Orchestrator for multi-turn retrieval-augmented conversation."""

    def __init__(
        self,
        session_store: Optional[BaseSessionStore] = None,
        retriever: Optional[EnterpriseHybridRetriever] = None,
        context_manager: Optional[ContextManager] = None,
        conversation_memory: Optional[ConversationMemory] = None,
        conversation_pruner: Optional[ConversationPruner] = None,
        extractive_provider: Optional[ExtractiveChatProvider] = None,
        local_llm_provider: Optional[LocalLLMChatProvider] = None,
        enterprise_provider: Optional[EnterpriseChatProvider] = None,
        default_mode: ExecutionMode = ExecutionMode.EXTRACTIVE,
    ) -> None:
        self.session_store = session_store or InMemorySessionStore()
        self.retriever = retriever
        self.context_manager = context_manager or ContextManager()
        self.conversation_memory = conversation_memory or ConversationMemory()
        self.conversation_pruner = conversation_pruner or ConversationPruner()

        self.extractive_provider = extractive_provider or ExtractiveChatProvider()
        self.local_llm_provider = local_llm_provider
        self.enterprise_provider = enterprise_provider
        self.default_mode = default_mode

        self._session_locks: Dict[str, threading.RLock] = defaultdict(threading.RLock)
        self._global_lock = threading.RLock()

    def _get_session_lock(self, session_key: str) -> threading.RLock:
        with self._global_lock:
            return self._session_locks[session_key]

    def chat(
        self,
        request: ChatTurnRequest,
    ) -> ChatResponse:
        """Processes a single conversational turn end-to-end."""
        clean_tenant = _validate_tenant_id(request.tenant_id, "ChatManager.chat.tenant_id")
        user_query = request.query.strip()
        if not user_query:
            raise ValueError("Query string must be non-empty.")

        # Step 1: Session resolution & Tenant Validation
        if hasattr(self.session_store, "create_or_get_session"):
            session = self.session_store.create_or_get_session(
                conversation_id=request.conversation_id,
                session_id=request.session_id,
                tenant_id=clean_tenant,
                user_id=request.user_id,
            )
        else:
            session = self.session_store.get_session(request.session_id or "", clean_tenant)
            if not session:
                session = ChatSession(
                    session_id=request.session_id or f"sess_{uuid.uuid4().hex[:16]}",
                    conversation_id=request.conversation_id or f"conv_{uuid.uuid4().hex[:16]}",
                    tenant_id=clean_tenant,
                    user_id=request.user_id,
                )
                session = self.session_store.create_session(session)

        # Enforce tenant isolation
        if session.tenant_id != clean_tenant:
            raise TenantBoundaryError(
                f"Session tenant '{session.tenant_id}' conflicts with request tenant '{clean_tenant}'."
            )

        session_lock = self._get_session_lock(f"{clean_tenant}:{session.session_id}")
        with session_lock:
            turn_id = f"turn_{uuid.uuid4().hex[:12]}"
            warnings: List[str] = []
            errors: List[str] = []

            # Step 2: Multi-turn Reference Resolution
            resolved_query, resolved_refs = self.conversation_memory.resolve_references(
                user_query, session
            )
            is_topic_switch = self.conversation_memory.detect_topic_switch(
                user_query, session
            )

            # Step 3: Untrusted Text & Prompt Injection Sanitization
            sanitized_query = sanitize_untrusted_text(user_query)

            # Step 4: Hybrid Retrieval
            retrieved_chunks = []
            if self.retriever is not None:
                search_filter = None
                if request.document_ids:
                    search_filter = HybridSearchFilter(document_ids=set(request.document_ids))
                try:
                    retrieved_chunks = self.retriever.retrieve(
                        query=resolved_query,
                        top_k=request.top_k,
                        filters=search_filter,
                    )
                except Exception as e:
                    warnings.append(f"Hybrid retrieval encountered an issue: {e}")

            # Step 5: Context Assembly & Token Budgeting
            assembled_context = self.context_manager.assemble_context(
                retrieved_items=retrieved_chunks,
                tenant_id=clean_tenant,
                allowed_document_ids=request.document_ids,
                max_tokens=request.max_tokens,
                expand_context=True,
                append_references=False,
            )

            # Step 6: Prune History for Prompt Synthesis
            pruned_history = self.conversation_pruner.prune_history(session.messages)

            # Step 7: Execution Mode Selection & Provider Invocation
            mode = request.mode or self.default_mode
            answer_text = ""
            token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

            if mode == ExecutionMode.EXTRACTIVE:
                answer_text, token_usage = self.extractive_provider.generate_response(
                    query=user_query,
                    context=assembled_context,
                    history=pruned_history,
                    system_instructions=request.system_instructions,
                    params=request.generation_params,
                )

            elif mode == ExecutionMode.LOCAL_LLM:
                if not self.local_llm_provider:
                    raise LocalLLMUnavailableError("Local LLM provider is not configured.")
                try:
                    answer_text, token_usage = self.local_llm_provider.generate_response(
                        query=user_query,
                        context=assembled_context,
                        history=pruned_history,
                        system_instructions=request.system_instructions,
                        params=request.generation_params,
                    )
                except Exception as e:
                    errors.append(str(e))
                    raise

            elif mode == ExecutionMode.ENTERPRISE:
                if not self.enterprise_provider:
                    raise EnterpriseProviderError("Enterprise provider is not configured.")
                try:
                    answer_text, token_usage = self.enterprise_provider.generate_response(
                        query=user_query,
                        context=assembled_context,
                        history=pruned_history,
                        system_instructions=request.system_instructions,
                        params=request.generation_params,
                    )
                except Exception as e:
                    errors.append(str(e))
                    raise

            # Step 8: Evidence & Citation Validation
            validation_result = self.context_manager.validate_evidence(
                response_text=answer_text,
                context_or_items=assembled_context,
            )

            # Step 9: Record Messages & Update Conversation Memory
            user_msg = ChatMessage(
                message_id=f"msg_{uuid.uuid4().hex[:12]}",
                turn_id=turn_id,
                role=MessageRole.USER,
                content=sanitized_query,
                timestamp=time.time(),
            )
            asst_msg = ChatMessage(
                message_id=f"msg_{uuid.uuid4().hex[:12]}",
                turn_id=turn_id,
                role=MessageRole.ASSISTANT,
                content=answer_text,
                citations=assembled_context.citations,
                evidence_references=[c.format_link() for c in assembled_context.citations],
                timestamp=time.time(),
                metadata={"execution_mode": mode.value},
            )

            session.messages.extend([user_msg, asst_msg])
            self.conversation_memory.update_session_memory(
                session=session,
                query=user_query,
                answer=answer_text,
                citations=assembled_context.citations,
            )

            # Persist updated session
            self.session_store.update_session(session)

            # Step 10: Build and return structured ChatResponse
            context_summary = (
                f"{len(assembled_context.included_chunks)} chunk(s) included, "
                f"{len(assembled_context.excluded_chunks)} chunk(s) excluded ({assembled_context.token_count} tokens)."
            )

            return ChatResponse(
                conversation_id=session.conversation_id,
                session_id=session.session_id,
                turn_id=turn_id,
                query=user_query,
                answer=answer_text,
                execution_mode=mode,
                citations=assembled_context.citations,
                evidence_references=[c.format_link() for c in assembled_context.citations],
                retrieved_chunks=assembled_context.included_chunks,
                token_usage=token_usage,
                context_summary=context_summary,
                validation_status=validation_result,
                warnings=warnings,
                errors=errors,
                timestamp=time.time(),
            )

    def delete_conversation(self, conversation_id: str, tenant_id: str) -> bool:
        """Deletes a conversation session and all its stored memory."""
        clean_tenant = _validate_tenant_id(tenant_id, "delete_conversation.tenant_id")
        if hasattr(self.session_store, "get_session_by_conversation"):
            sess = self.session_store.get_session_by_conversation(conversation_id, clean_tenant)
            if sess:
                return self.session_store.delete_session(sess.session_id, clean_tenant)
        return False
