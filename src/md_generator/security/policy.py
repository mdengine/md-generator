from __future__ import annotations

"""Security Policy Engine for md_generator.

Phase 0B-4 Implementation: Standard library only security policy rules,
configurable secret/PII redaction policies, and network identifier flags.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Set
import json

from md_generator.semantic.model.schema import InvalidSchemaError, _check_no_unknown_fields


@dataclass
class SecurityPolicy:
    enable_secret_redaction: bool = True
    enable_credential_masking: bool = True
    enable_pii_masking: bool = True
    mask_network_identifiers: bool = False  # Configurable for IP addresses in Log/OTEL environments
    mask_financial_data: bool = True
    custom_patterns: List[Dict[str, str]] = field(default_factory=list)
    persist_original_content: bool = False  # Ephemeral raw content enforcement

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not isinstance(self.enable_secret_redaction, bool):
            raise InvalidSchemaError("SecurityPolicy.enable_secret_redaction must be a boolean.")
        if not isinstance(self.mask_network_identifiers, bool):
            raise InvalidSchemaError("SecurityPolicy.mask_network_identifiers must be a boolean.")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SecurityPolicy:
        if not isinstance(data, dict):
            raise InvalidSchemaError("Input to from_dict must be a dictionary.")
        allowed = set(cls.__dataclass_fields__.keys())
        _check_no_unknown_fields(data, allowed, "SecurityPolicy")
        try:
            return cls(**data)
        except (TypeError, ValueError) as e:
            raise InvalidSchemaError(f"Failed to instantiate SecurityPolicy: {e}") from e

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> SecurityPolicy:
        try:
            return cls.from_dict(json.loads(json_str))
        except json.JSONDecodeError as e:
            raise InvalidSchemaError(f"Invalid JSON format for SecurityPolicy: {e}") from e
