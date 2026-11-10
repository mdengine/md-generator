"""Contract Tests for SecurityRedactor & SecurityFinding Audit Tracking."""

import pytest
from md_generator.security import SecurityPolicy, SecurityFinding, SecurityRedactor


def test_redactor_aws_key_redaction():
    text = "AWS_KEY=AKIA1234567890ABCDEF in config"
    redactor = SecurityRedactor()
    res = redactor.redact(text)

    assert "[REDACTED_AWS_KEY]" in res.sanitized_content
    assert "AKIA1234567890ABCDEF" not in res.sanitized_content
    assert len(res.findings) == 1
    assert res.findings[0].category == "SECRET"
    assert res.findings[0].rule_id == "AWS_ACCESS_KEY"


def test_redactor_password_and_email():
    text = "user email: dev@company.com, db_password='SecretPassword123'"
    redactor = SecurityRedactor()
    res = redactor.redact(text)

    assert "[MASKED_EMAIL]" in res.sanitized_content
    assert "[REDACTED_PASSWORD]" in res.sanitized_content
    assert res.metadata.secrets_redacted_count >= 1
    assert res.metadata.pii_masked_count >= 1


def test_redactor_network_identifiers_toggle():
    text = "Connected from IP: 192.168.1.50"
    
    # By default, IP address masking is disabled (mask_network_identifiers=False for log observability)
    redactor_disabled = SecurityRedactor(SecurityPolicy(mask_network_identifiers=False))
    res_disabled = redactor_disabled.redact(text)
    assert "192.168.1.50" in res_disabled.sanitized_content

    # When enabled, IP address is masked
    redactor_enabled = SecurityRedactor(SecurityPolicy(mask_network_identifiers=True))
    res_enabled = redactor_enabled.redact(text)
    assert "[MASKED_IP]" in res_enabled.sanitized_content
    assert "192.168.1.50" not in res_enabled.sanitized_content
