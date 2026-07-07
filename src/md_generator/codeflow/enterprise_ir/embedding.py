from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EmbeddingMetadata:
    model_name: str
    dimension: int
    metric: str  # e.g., "cosine", "l2"
    created_at: str
    additional_info: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingResult:
    entity_id: str
    vector: list[float]
    metadata: EmbeddingMetadata


class EmbeddingProvider(ABC):
    @abstractmethod
    def generate_embedding(self, text: str) -> list[float]:
        """Generates a dense vector representation for the given text."""
        pass

    @abstractmethod
    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generates dense vector representations for a batch of texts."""
        pass


class EmbeddingStorage(ABC):
    @abstractmethod
    def store_embedding(self, entity_id: str, vector: list[float], metadata: EmbeddingMetadata) -> None:
        """Stores a vector embedding associated with an entity ID."""
        pass

    @abstractmethod
    def query_similarity(self, vector: list[float], top_k: int = 10) -> list[tuple[str, float]]:
        """Queries the vector database and returns top-K nearest entity IDs and their similarity scores."""
        pass
