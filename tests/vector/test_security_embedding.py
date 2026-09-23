"""Unit tests for raw secret leak prevention and recursive secret stripping in fingerprints."""

from md_generator.vector.processor import (
    sanitize_config_recursive,
    compute_embedding_processing_fingerprint,
)
from md_generator.vector.providers.mock import MockEmbeddingProvider


def test_security_raw_secret_leak_prevention_in_provider():
    provider = MockEmbeddingProvider()
    # Unredacted secret in raw string
    raw_texts = ["API_KEY=sk-proj-1234567890abcdef Secret Passphrase"]
    
    # Provider generates float vector, raw text is converted to floats deterministically
    vectors = provider.embed_texts(raw_texts)
    assert len(vectors) == 1
    assert isinstance(vectors[0], list)
    # Ensure float vector contains only floats
    for val in vectors[0]:
        assert isinstance(val, float)


def test_security_recursive_secret_stripping_case_insensitive():
    config = {
        "API_KEY": "secret_key_val",
        "nested": {
            "Access_Token": "token_val",
            "normal_setting": "enabled",
        },
        "list_items": [
            {"Bearer_Token": "bearer_val"},
            {"public_param": "ok"},
        ],
    }

    sanitized = sanitize_config_recursive(config)
    assert "API_KEY" not in sanitized
    assert "Access_Token" not in sanitized["nested"]
    assert "Bearer_Token" not in sanitized["list_items"][0]
    assert sanitized["nested"]["normal_setting"] == "enabled"
    assert sanitized["list_items"][1]["public_param"] == "ok"

    # Fingerprint does not change when secret values rotate
    config_v1 = {"api_key": "key_1", "model": "gpt-4"}
    config_v2 = {"api_key": "key_2", "model": "gpt-4"}

    p = MockEmbeddingProvider()
    fp1 = compute_embedding_processing_fingerprint(p, config_v1)
    fp2 = compute_embedding_processing_fingerprint(p, config_v2)

    assert fp1 == fp2
