"""OpenAI embedding provider adapter with dynamic optional import handling."""

from typing import List, Optional, Any
from md_generator.vector.exceptions import EmbeddingProviderError
from md_generator.vector.providers.base import BaseEmbeddingProvider, ProviderRegistry


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Optional adapter for OpenAI / Azure OpenAI embedding models."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "text-embedding-3-small",
        model_version: str = "3.0",
        dimension: int = 1536,
        max_batch_size: int = 100,
        api_base: Optional[str] = None,
    ) -> None:
        try:
            import openai  # type: ignore
            self._client = openai.OpenAI(api_key=api_key, base_url=api_base) if api_key else None
        except Exception as e:
            raise EmbeddingProviderError(
                f"openai package is not available or failed to load: {e}"
            ) from e

        self._model_name = model_name
        self._model_version = model_version
        self._dimension = dimension
        self._max_batch_size = max_batch_size

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def max_batch_size(self) -> int:
        return self._max_batch_size

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not isinstance(texts, list):
            raise EmbeddingProviderError("Input texts must be a list of strings.")
        if len(texts) == 0:
            return []
        if len(texts) > self.max_batch_size:
            raise EmbeddingProviderError(
                f"Batch size {len(texts)} exceeds provider max_batch_size {self.max_batch_size}."
            )
        if self._client is None:
            raise EmbeddingProviderError("OpenAI client is not initialized with a valid API key.")

        try:
            response = self._client.embeddings.create(input=texts, model=self.model_name)
            return [data.embedding for data in response.data]
        except Exception as e:
            raise EmbeddingProviderError(f"Failed to generate OpenAI embeddings: {e}") from e


ProviderRegistry.register("openai", OpenAIEmbeddingProvider)
