"""Unit tests for MockEmbeddingProvider and ProviderRegistry."""

import pytest
from md_generator.vector.exceptions import EmbeddingProviderError
from md_generator.vector.providers import MockEmbeddingProvider, ProviderRegistry


def test_mock_provider_determinism():
    p1 = MockEmbeddingProvider(dimension=128)
    p2 = MockEmbeddingProvider(dimension=128)

    texts = ["enterprise architecture", "tree-sitter ast chunking"]
    res1 = p1.embed_texts(texts)
    res2 = p2.embed_texts(texts)

    assert len(res1) == 2
    assert len(res2) == 2
    assert len(res1[0]) == 128
    assert res1[0] == res2[0]
    assert res1[1] == res2[1]


def test_mock_provider_empty_input():
    provider = MockEmbeddingProvider()
    assert provider.embed_texts([]) == []


def test_mock_provider_batch_size_exceeded():
    provider = MockEmbeddingProvider(max_batch_size=2)
    with pytest.raises(EmbeddingProviderError, match="exceeds provider max_batch_size"):
        provider.embed_texts(["a", "b", "c"])


def test_provider_registry():
    provider_cls = ProviderRegistry.get("mock")
    assert provider_cls == MockEmbeddingProvider
    assert "mock" in ProviderRegistry.list_providers()

    with pytest.raises(EmbeddingProviderError, match="is not registered"):
        ProviderRegistry.get("unknown_provider")
