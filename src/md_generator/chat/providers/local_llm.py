from __future__ import annotations

"""Local LLM Chat Provider: Ollama & Local Inference Endpoints.

Phase 2D/Prompt 06 Implementation:
- Standard OpenAI-compatible API client using Python standard library (urllib).
- Supports local inference engines: Ollama, vLLM, llama.cpp, LocalAI.
- Explicit error handling: never silently downgrades on provider unavailability.
"""

import json
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.request

from md_generator.adapters.langchain.context import estimate_token_count
from md_generator.chat.models import ChatMessage, MessageRole
from md_generator.chat.providers.base import BaseChatProvider
from md_generator.context.manager import AssembledContext


class LocalLLMUnavailableError(Exception):
    """Raised when the local LLM server is unreachable, timed out, or returns a fault."""
    pass


class LocalLLMChatProvider(BaseChatProvider):
    """Integrates local OpenAI-compatible inference servers without third-party dependencies."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model: str = "llama3",
        timeout_seconds: float = 30.0,
        temperature: float = 0.2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature

    def generate_response(
        self,
        query: str,
        context: AssembledContext,
        history: List[ChatMessage],
        system_instructions: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, int]]:
        """Invokes local LLM endpoint with assembled context and conversation history."""
        effective_params = dict(params or {})
        temp = float(effective_params.get("temperature", self.temperature))
        max_tokens = int(effective_params.get("max_tokens", 1024))

        # Format system message
        sys_prompt_parts = [
            system_instructions or "You are an enterprise assistant. Answer accurately using only the provided context."
        ]
        if context.context_text:
            sys_prompt_parts.append("\n=== Document Context ===\n")
            sys_prompt_parts.append(context.context_text)

        messages_payload: List[Dict[str, str]] = [
            {"role": "system", "content": "\n".join(sys_prompt_parts)}
        ]

        # Append recent history
        for msg in history:
            role_str = "user" if msg.role == MessageRole.USER else "assistant"
            messages_payload.append({"role": role_str, "content": msg.content})

        # Append current user query
        messages_payload.append({"role": "user", "content": query})

        payload_data = {
            "model": self.model,
            "messages": messages_payload,
            "temperature": temp,
            "max_tokens": max_tokens,
            "stream": False,
        }

        endpoint = f"{self.base_url}/chat/completions"
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload_data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))
                choice = resp_json.get("choices", [{}])[0]
                content = choice.get("message", {}).get("content", "")
                usage = resp_json.get("usage", {})
                prompt_tok = usage.get("prompt_tokens", context.token_count)
                comp_tok = usage.get("completion_tokens", estimate_token_count(content))
                total_tok = usage.get("total_tokens", prompt_tok + comp_tok)

                return content, {
                    "prompt_tokens": prompt_tok,
                    "completion_tokens": comp_tok,
                    "total_tokens": total_tok,
                }

        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
            raise LocalLLMUnavailableError(
                f"Local LLM provider at '{endpoint}' is unavailable or failed: {e}"
            ) from e
