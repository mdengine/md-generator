from __future__ import annotations

"""Security Finding & Redactor Module for md_generator.

Phase 0B-4 Implementation: Standard library regex security detection,
finding audit tracking, and secret/PII redaction transformation.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
import json
import re

from md_generator.semantic.model.schema import InvalidSchemaError, SecurityMetadata, _check_no_unknown_fields
from md_generator.security.policy import SecurityPolicy


@dataclass
class SecurityFinding:
    category: str        # 'SECRET', 'CREDENTIAL', 'PII', 'FINANCIAL', 'NETWORK_IDENTIFIER'
    rule_id: str         # 'AWS_ACCESS_KEY', 'DB_PASSWORD', 'BEARER_TOKEN', 'EMAIL_ADDRESS', 'IP_ADDRESS'
    line_number: Optional[int] = None
    confidence: float = 1.0
    replacement: str = "[REDACTED]"
    action: str = "REDACTED"

    def __post_init__(self) -> None:
        if not self.category or not isinstance(self.category, str):
            raise InvalidSchemaError("SecurityFinding.category must be a non-empty string.")
        if not self.rule_id or not isinstance(self.rule_id, str):
            raise InvalidSchemaError("SecurityFinding.rule_id must be a non-empty string.")

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SecurityFinding:
        if not isinstance(data, dict):
            raise InvalidSchemaError("Input to from_dict must be a dictionary.")
        allowed = set(cls.__dataclass_fields__.keys())
        _check_no_unknown_fields(data, allowed, "SecurityFinding")
        try:
            return cls(**data)
        except (TypeError, ValueError) as e:
            raise InvalidSchemaError(f"Failed to instantiate SecurityFinding: {e}") from e


@dataclass
class RedactionResult:
    sanitized_content: str
    findings: List[SecurityFinding]
    metadata: SecurityMetadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sanitized_content": self.sanitized_content,
            "findings": [f.to_dict() for f in self.findings],
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RedactionResult:
        if not isinstance(data, dict):
            raise InvalidSchemaError("Input to from_dict must be a dictionary.")
        allowed = set(cls.__dataclass_fields__.keys())
        _check_no_unknown_fields(data, allowed, "RedactionResult")
        try:
            findings = [SecurityFinding.from_dict(f) for f in data.get("findings", [])]
            meta = SecurityMetadata.from_dict(data["metadata"]) if data.get("metadata") else SecurityMetadata()
            return cls(
                sanitized_content=data.get("sanitized_content", ""),
                findings=findings,
                metadata=meta,
            )
        except (TypeError, ValueError) as e:
            raise InvalidSchemaError(f"Failed to instantiate RedactionResult: {e}") from e


# Standard regex detection rules
_AWS_KEY_PATTERN = re.compile(r"\b(AKIA[0-9A-Z]{16})\b")
_RSA_KEY_PATTERN = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
_BEARER_TOKEN_PATTERN = re.compile(r"\b(Bearer\s+[A-Za-z0-9\-._~+/]+=*)\b", re.IGNORECASE)
_PASSWORD_CONN_PATTERN = re.compile(r"(password|pwd|pass)\s*[:=]\s*['\"]?([^\s'\";]+)['\"]?", re.IGNORECASE)
_EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_IP_ADDRESS_PATTERN = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
_CREDIT_CARD_PATTERN = re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b")


class SecurityRedactor:
    """Standard library regex redactor performing security pattern analysis."""

    def __init__(self, policy: Optional[SecurityPolicy] = None) -> None:
        self.policy = policy or SecurityPolicy()

    def redact(self, content: str) -> RedactionResult:
        if not isinstance(content, str):
            raise InvalidSchemaError("Content must be a string.")

        findings: List[SecurityFinding] = []
        sanitized = content
        rules_applied: List[str] = []

        # 1. AWS Access Keys
        if self.policy.enable_secret_redaction:
            for match in _AWS_KEY_PATTERN.finditer(sanitized):
                findings.append(
                    SecurityFinding(
                        category="SECRET",
                        rule_id="AWS_ACCESS_KEY",
                        confidence=1.0,
                        replacement="[REDACTED_AWS_KEY]",
                        action="REDACTED",
                    )
                )
            sanitized = _AWS_KEY_PATTERN.sub("[REDACTED_AWS_KEY]", sanitized)

            # RSA Private Keys
            if _RSA_KEY_PATTERN.search(sanitized):
                findings.append(
                    SecurityFinding(
                        category="SECRET",
                        rule_id="RSA_PRIVATE_KEY",
                        confidence=1.0,
                        replacement="[REDACTED_PRIVATE_KEY]",
                        action="REDACTED",
                    )
                )
                sanitized = _RSA_KEY_PATTERN.sub("[REDACTED_PRIVATE_KEY]", sanitized)
            rules_applied.append("SECRET_REDACTION")

        # 2. Credentials (Bearer tokens, Passwords)
        if self.policy.enable_credential_masking:
            for match in _BEARER_TOKEN_PATTERN.finditer(sanitized):
                findings.append(
                    SecurityFinding(
                        category="CREDENTIAL",
                        rule_id="BEARER_TOKEN",
                        confidence=0.95,
                        replacement="Bearer [REDACTED_TOKEN]",
                        action="MASKED",
                    )
                )
            sanitized = _BEARER_TOKEN_PATTERN.sub("Bearer [REDACTED_TOKEN]", sanitized)

            for match in _PASSWORD_CONN_PATTERN.finditer(sanitized):
                findings.append(
                    SecurityFinding(
                        category="CREDENTIAL",
                        rule_id="DB_PASSWORD",
                        confidence=0.90,
                        replacement=r"\1=[REDACTED_PASSWORD]",
                        action="MASKED",
                    )
                )
            sanitized = _PASSWORD_CONN_PATTERN.sub(r"\1=[REDACTED_PASSWORD]", sanitized)
            rules_applied.append("CREDENTIAL_MASKING")

        # 3. PII (Emails)
        if self.policy.enable_pii_masking:
            for match in _EMAIL_PATTERN.finditer(sanitized):
                findings.append(
                    SecurityFinding(
                        category="PII",
                        rule_id="EMAIL_ADDRESS",
                        confidence=1.0,
                        replacement="[MASKED_EMAIL]",
                        action="MASKED",
                    )
                )
            sanitized = _EMAIL_PATTERN.sub("[MASKED_EMAIL]", sanitized)
            rules_applied.append("PII_MASKING")

        # 4. Financial (Credit Cards)
        if self.policy.mask_financial_data:
            for match in _CREDIT_CARD_PATTERN.finditer(sanitized):
                findings.append(
                    SecurityFinding(
                        category="FINANCIAL",
                        rule_id="CREDIT_CARD",
                        confidence=1.0,
                        replacement="[REDACTED_CARD]",
                        action="REDACTED",
                    )
                )
            sanitized = _CREDIT_CARD_PATTERN.sub("[REDACTED_CARD]", sanitized)
            rules_applied.append("FINANCIAL_MASKING")

        # 5. Network Identifiers (IP addresses if enabled)
        if self.policy.mask_network_identifiers:
            for match in _IP_ADDRESS_PATTERN.finditer(sanitized):
                findings.append(
                    SecurityFinding(
                        category="NETWORK_IDENTIFIER",
                        rule_id="IP_ADDRESS",
                        confidence=0.95,
                        replacement="[MASKED_IP]",
                        action="MASKED",
                    )
                )
            sanitized = _IP_ADDRESS_PATTERN.sub("[MASKED_IP]", sanitized)
            rules_applied.append("NETWORK_IDENTIFIER_MASKING")

        # 6. Custom Patterns
        for custom in self.policy.custom_patterns:
            name = custom.get("name", "CUSTOM_RULE")
            pattern_str = custom.get("regex", "")
            replacement = custom.get("replacement", "[REDACTED_CUSTOM]")
            if pattern_str:
                rx = re.compile(pattern_str)
                if rx.search(sanitized):
                    findings.append(
                        SecurityFinding(
                            category="CUSTOM",
                            rule_id=name,
                            confidence=1.0,
                            replacement=replacement,
                            action="REDACTED",
                        )
                    )
                    sanitized = rx.sub(replacement, sanitized)

        secrets_cnt = sum(1 for f in findings if f.category in ("SECRET", "CREDENTIAL"))
        pii_cnt = sum(1 for f in findings if f.category in ("PII", "FINANCIAL", "NETWORK_IDENTIFIER"))

        metadata = SecurityMetadata(
            is_sanitized=True,
            secrets_redacted_count=secrets_cnt,
            pii_masked_count=pii_cnt,
            applied_rules=rules_applied,
        )

        return RedactionResult(
            sanitized_content=sanitized,
            findings=findings,
            metadata=metadata,
        )
