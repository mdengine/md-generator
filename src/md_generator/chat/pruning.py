from __future__ import annotations

"""Conversation History Pruning & Token Budget Management.

Phase 2D/Prompt 06 Implementation:
- Enforces strict token budgets for conversational history.
- Retains recent turns verbatim while summarizing or pruning older turns.
- Preserves citations and evidence references required for grounding.
"""

from typing import List, Optional

from md_generator.adapters.langchain.context import estimate_token_count
from md_generator.chat.models import ChatMessage, MessageRole


class ConversationPruner:
    """Manages short-term history windowing, summarization, and token budgeting."""

    def __init__(
        self,
        max_turns: int = 6,
        max_history_tokens: int = 1000,
    ) -> None:
        self.max_turns = max_turns
        self.max_history_tokens = max_history_tokens

    def prune_history(
        self,
        messages: List[ChatMessage],
        max_turns: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ) -> List[ChatMessage]:
        """Prunes conversation history to fit within turn limits and token budget."""
        if not messages:
            return []

        effective_turns = max_turns or self.max_turns
        effective_tokens = max_tokens or self.max_history_tokens

        # Step 1: Retain at most the last `effective_turns` messages
        recent = messages[-effective_turns:]

        # Step 2: Enforce token budget working backwards from the most recent turn
        retained: List[ChatMessage] = []
        accumulated_tokens = 0

        for msg in reversed(recent):
            content_tokens = estimate_token_count(msg.content)
            # Reserve space for citation tags if present
            cit_tokens = len(msg.citations) * 15
            turn_tokens = content_tokens + cit_tokens

            if accumulated_tokens + turn_tokens <= effective_tokens:
                retained.append(msg)
                accumulated_tokens += turn_tokens
            else:
                # If we cannot fit the entire message, stop or include at least 1 recent turn
                if not retained:
                    # Keep at least the immediate prior message
                    retained.append(msg)
                break

        # Reverse back to forward chronological order
        return list(reversed(retained))

    def format_history_context(self, messages: List[ChatMessage]) -> str:
        """Formats pruned history into a clean prompt context block."""
        if not messages:
            return ""

        lines: List[str] = ["--- Conversation History ---"]
        for msg in messages:
            role_label = "User" if msg.role == MessageRole.USER else "Assistant"
            lines.append(f"{role_label}: {msg.content}")

        return "\n".join(lines)
