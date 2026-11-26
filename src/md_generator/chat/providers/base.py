from __future__ import annotations

"""Abstract Base Provider for Multi-turn Conversational Chat Generation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from md_generator.chat.models import ChatMessage
from md_generator.context.manager import AssembledContext


class BaseChatProvider(ABC):
    """Abstract interface for generating answers from query, assembled context, and history."""

    @abstractmethod
    def generate_response(
        self,
        query: str,
        context: AssembledContext,
        history: List[ChatMessage],
        system_instructions: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, int]]:
        """Generates an answer string and reports token usage dict.
        
        Returns:
            Tuple[str, Dict[str, int]]: (answer_text, {"prompt_tokens": N, "completion_tokens": M, "total_tokens": N+M})
        """
        pass
