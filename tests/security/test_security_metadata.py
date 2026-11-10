"""Contract & Verification Tests for SecurityMetadata and Ephemeral Content."""

import pytest
from md_generator.semantic.model.schema import SecurityMetadata
from md_generator.security import SecurityPolicy, SecurityRedactor


def test_security_metadata_creation_and_counts():
    text = "AWS Key AKIA1234567890ABCDEF and email test@company.com"
    redactor = SecurityRedactor()
    res = redactor.redact(text)

    assert isinstance(res.metadata, SecurityMetadata)
    assert res.metadata.is_sanitized is True
    assert res.metadata.secrets_redacted_count == 1
    assert res.metadata.pii_masked_count == 1
    assert "SECRET_REDACTION" in res.metadata.applied_rules
    assert "PII_MASKING" in res.metadata.applied_rules


def test_ephemeral_raw_content_enforcement():
    raw_content = "Secret: AKIA1234567890ABCDEF"
    policy = SecurityPolicy(persist_original_content=False)
    redactor = SecurityRedactor(policy)
    res = redactor.redact(raw_content)

    # Verify original_content is sanitized and sensitive value is not in output
    assert "AKIA1234567890ABCDEF" not in res.sanitized_content
    assert "[REDACTED_AWS_KEY]" in res.sanitized_content
    assert res.metadata.is_sanitized is True
