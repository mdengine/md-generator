"""SentenceTransformers embedding provider adapter with dynamic optional import handling."""

from typing import List, Any
from md_generator.vector.exceptions import EmbeddingProviderError
from md_generator.vector.providers.base import BaseEmbeddingProvider, ProviderRegistry


class SentenceTransformersEmbeddingProvider(BaseEmbeddingProvider):
    """Optional adapter for local SentenceTransformers embedding models."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        model_version: str = "1.0",
        dimension: int = 384,
        max_batch_size: int = 64,
        device: str = "cpu",
    ) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            self._model = SentenceTransformer(model_name, device=device)
        except Exception as e:
            raise EmbeddingProviderError(
                f"sentence_transformers package is not available or failed to load: {e}"
            ) from e

        self._model_name = model_name
        self._model_version = model_version
        self._dimension = dimension
        self._max_batch_size = max_batch_size

    @property
    def provider_name(self) -> str:
        return "sentence_transformers"

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

        try:
            embeddings = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return [vec.tolist() for vec in embeddings]
        except Exception as e:
            raise EmbeddingProviderError(f"Failed to generate SentenceTransformers embeddings: {e}") from e


ProviderRegistry.register("sentence_transformers", SentenceTransformersEmbeddingProvider)
