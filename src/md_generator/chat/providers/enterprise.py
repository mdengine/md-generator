from __future__ import annotations

"""Enterprise Intelligence Chat Provider: Secure Adapters for Enterprise Gateways.

Phase 2D/Prompt 06 Implementation:
- Secure connection to enterprise AI gateways and LLM proxy endpoints.
- Strict credential protection: API keys never logged, committed, or exposed.
- Explicit error handling for timeouts, rate limits, and network faults.
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.request

from md_generator.adapters.langchain.context import estimate_token_count
from md_generator.chat.models import ChatMessage, MessageRole
from md_generator.chat.providers.base import BaseChatProvider
from md_generator.context.manager import AssembledContext


class EnterpriseProviderError(Exception):
    """Raised when the enterprise LLM provider encounters an API error, timeout, or rate limit."""
    pass


class EnterpriseChatProvider(BaseChatProvider):
    """Secure adapter for enterprise LLM endpoints."""

    def __init__(
        self,
        api_base_url: str,
        model: str = "enterprise-default",
        api_key: Optional[str] = None,
        timeout_seconds: float = 60.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.api_base_url = api_base_url.rstrip("/")
        self.model = model
        self.api_key = api_key or os.environ.get("ENTERPRISE_LLM_API_KEY")
        self.timeout_seconds = timeout_seconds
        self.custom_headers = dict(headers or {})

    def generate_response(
        self,
        query: str,
        context: AssembledContext,
        history: List[ChatMessage],
        system_instructions: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, int]]:
        """Invokes enterprise LLM gateway with context and conversation history."""
        effective_params = dict(params or {})
        temp = float(effective_params.get("temperature", 0.1))
        max_tokens = int(effective_params.get("max_tokens", 2048))

        sys_prompt_parts = [
            system_instructions or "You are an enterprise AI assistant. Ground all statements in the provided context and citations."
        ]
        if context.context_text:
            sys_prompt_parts.append("\n=== Document Context ===\n")
            sys_prompt_parts.append(context.context_text)

        messages_payload: List[Dict[str, str]] = [
            {"role": "system", "content": "\n".join(sys_prompt_parts)}
        ]

        for msg in history:
            role_str = "user" if msg.role == MessageRole.USER else "assistant"
            messages_payload.append({"role": role_str, "content": msg.content})

        messages_payload.append({"role": "user", "content": query})

        payload_data = {
            "model": self.model,
            "messages": messages_payload,
            "temperature": temp,
            "max_tokens": max_tokens,
            "stream": False,
        }

        endpoint = f"{self.api_base_url}/chat/completions"
        req_headers = {"Content-Type": "application/json"}
        req_headers.update(self.custom_headers)

        if self.api_key:
            req_headers["Authorization"] = f"Bearer {self.api_key}"

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload_data).encode("utf-8"),
            headers=req_headers,
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

        except urllib.error.HTTPError as e:
            # Mask API key from error diagnostics
            raise EnterpriseProviderError(
                f"Enterprise provider HTTP error {e.code} at endpoint '{self.api_base_url}': {e.reason}"
            ) from e
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            raise EnterpriseProviderError(
                f"Enterprise provider connection error at endpoint '{self.api_base_url}': {e}"
            ) from e
