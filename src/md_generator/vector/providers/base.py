"""BaseEmbeddingProvider protocol and provider registry."""

from typing import Protocol, List, Dict, Type, Any
from md_generator.vector.exceptions import EmbeddingProviderError


class BaseEmbeddingProvider(Protocol):
    """Protocol for embedding model providers."""

    @property
    def provider_name(self) -> str:
        ...

    @property
    def model_name(self) -> str:
        ...

    @property
    def model_version(self) -> str:
        ...

    @property
    def dimension(self) -> int:
        ...

    @property
    def max_batch_size(self) -> int:
        ...

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        ...


class ProviderRegistry:
    """Registry for pluggable embedding engine providers."""

    _providers: Dict[str, Type[Any]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: Type[Any]) -> None:
        cls._providers[name.lower()] = provider_cls

    @classmethod
    def get(cls, name: str) -> Type[Any]:
        key = name.lower()
        if key not in cls._providers:
            raise EmbeddingProviderError(f"Embedding provider '{name}' is not registered.")
        return cls._providers[key]

    @classmethod
    def list_providers(cls) -> List[str]:
        return sorted(list(cls._providers.keys()))
