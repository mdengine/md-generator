"""Contract Tests for SecurityPolicy Serialization and Invariants."""

import pytest
from md_generator.semantic.model.schema import InvalidSchemaError
from md_generator.security import SecurityPolicy


def test_security_policy_defaults():
    policy = SecurityPolicy()
    assert policy.enable_secret_redaction is True
    assert policy.enable_credential_masking is True
    assert policy.enable_pii_masking is True
    assert policy.mask_network_identifiers is False  # Default IP masking disabled for logs
    assert policy.persist_original_content is False  # Ephemeral raw content enforcement


def test_security_policy_unknown_field_rejection():
    data = {"enable_secret_redaction": True, "disallowed_rule": "val"}
    with pytest.raises(InvalidSchemaError, match=r"Unknown fields for SecurityPolicy: \['disallowed_rule'\]"):
        SecurityPolicy.from_dict(data)


def test_security_policy_serialization_roundtrip():
    policy = SecurityPolicy(
        mask_network_identifiers=True,
        custom_patterns=[{"name": "INTERNAL_ID", "regex": r"ID-[0-9]+", "replacement": "[REDACTED_ID]"}],
    )
    d = policy.to_dict()
    reconstructed = SecurityPolicy.from_dict(d)
    assert reconstructed.mask_network_identifiers is True
    assert reconstructed.custom_patterns == policy.custom_patterns
    assert reconstructed.to_json() == policy.to_json()
