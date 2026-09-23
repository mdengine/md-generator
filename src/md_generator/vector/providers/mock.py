"""Deterministic standard library mock embedding provider for testing and offline execution."""

import hashlib
import math
from typing import List

from md_generator.vector.exceptions import EmbeddingProviderError
from md_generator.vector.model import EMBEDDING_ID_ALGORITHM_VERSION
from md_generator.vector.providers.base import BaseEmbeddingProvider, ProviderRegistry


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic stdlib embedding provider generating process-independent pseudo-random float vectors."""

    def __init__(
        self,
        dimension: int = 384,
        model_name: str = "mock-embedding-v1",
        model_version: str = "1.0",
        max_batch_size: int = 256,
    ) -> None:
        if dimension <= 0:
            raise EmbeddingProviderError("Dimension must be a positive integer.")
        if max_batch_size <= 0:
            raise EmbeddingProviderError("Max batch size must be a positive integer.")
        self._dimension = dimension
        self._model_name = model_name
        self._model_version = model_version
        self._max_batch_size = max_batch_size

    @property
    def provider_name(self) -> str:
        return "mock"

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

        results: List[List[float]] = []
        for text in texts:
            if not isinstance(text, str):
                raise EmbeddingProviderError(f"Text entry must be a string, got {type(text)}.")
            vector: List[float] = []
            for dim_idx in range(self.dimension):
                seed_str = f"{EMBEDDING_ID_ALGORITHM_VERSION}:{text}:{self.model_name}:{self.dimension}:{dim_idx}"
                digest = hashlib.sha256(seed_str.encode("utf-8")).digest()
                # Convert first 4 bytes to an integer and scale to [-1.0, 1.0]
                val_int = int.from_bytes(digest[:4], byteorder="big", signed=False)
                val_float = (val_int / (2**32 - 1)) * 2.0 - 1.0
                vector.append(val_float)
            
            # Ensure non-zero norm
            norm = math.hypot(*vector)
            if norm == 0.0:
                vector[0] = 1.0
            results.append(vector)

        return results


ProviderRegistry.register("mock", MockEmbeddingProvider)
