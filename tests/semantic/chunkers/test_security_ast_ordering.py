"""Tests for security redaction ordering and secret leak prevention in AST analysis."""

import hashlib
from md_generator.security.policy import SecurityPolicy
from md_generator.security.redactor import SecurityRedactor
from md_generator.semantic.processor import SemanticProcessor
from md_generator.semantic.model.schema import CanonicalMetadata, SemanticDocument


def _make_doc_id(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def test_security_redaction_before_ast_analysis():
    raw_code = """class DatabaseConfig:
    def connect(self):
        password = "secret_password_12345"
        aws_key = "AKIAIOSFODNN7EXAMPLE"
        print(password, aws_key)
"""

    policy = SecurityPolicy(enable_secret_redaction=True, enable_credential_masking=True)
    redactor = SecurityRedactor(policy)
    redaction_res = redactor.redact(raw_code)
    redacted_content = redaction_res.sanitized_content

    assert "secret_password_12345" not in redacted_content
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted_content
    assert "[REDACTED_PASSWORD]" in redacted_content
    assert "[REDACTED_AWS_KEY]" in redacted_content

    doc = SemanticDocument(
        document_id=_make_doc_id("doc-sec-1"),
        sanitized_content=redacted_content,
        metadata=CanonicalMetadata(source_uri="file:///db_config.py", source_type="py", language="python"),
    )

    processor = SemanticProcessor()
    res = processor.process_documents([doc])

    res_dict_str = str(res.to_dict())
    assert "secret_password_12345" not in res_dict_str
    assert "AKIAIOSFODNN7EXAMPLE" not in res_dict_str

    assert len(res.chunks) >= 1
