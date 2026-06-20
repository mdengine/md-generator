from __future__ import annotations

from pathlib import Path

from md_generator.codeflow.adapters.base import LanguageAdapter


class LanguageAdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, LanguageAdapter] = {}

    def register(self, adapter: LanguageAdapter) -> None:
        for ext in adapter.supported_extensions:
            self._adapters[ext.lower()] = adapter

    def get_adapter_for_path(self, path: Path) -> LanguageAdapter | None:
        ext = path.suffix.lower()
        return self._adapters.get(ext)

    def list_adapters(self) -> list[LanguageAdapter]:
        seen = set()
        res = []
        for a in self._adapters.values():
            if a not in seen:
                seen.add(a)
                res.append(a)
        return res

    def select_backend(self, adapter: LanguageAdapter, preferred_backend: str | None = None) -> str:
        """Selects parser backend following hierarchy: Preferred -> Adapter Priority -> fallback 'regex'."""
        backends = adapter.parser_backends
        if preferred_backend and preferred_backend in backends:
            return preferred_backend
        if backends:
            return backends[0]
        return "regex"
