from __future__ import annotations

"""Enterprise Metadata & Tenant Boundary Schema for md_generator.

Phase 0B-1 Implementation: Standard library only enterprise metadata schema
with mandatory tenant isolation boundary.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set
import json

from md_generator.semantic.model.schema import SCHEMA_VERSION, InvalidSchemaError


def _check_no_unknown_fields(data: Dict[str, Any], allowed_fields: Set[str], model_name: str) -> None:
    unknown = set(data.keys()) - allowed_fields
    if unknown:
        raise InvalidSchemaError(f"Unknown fields for {model_name}: {sorted(list(unknown))}")


@dataclass
class EnterpriseMetadata:
    # Source Identity
    repository: str = ""
    source_uri: str = ""
    source_type: str = "generic"

    # Enterprise Context
    system: str = "default"
    application: str = "default"
    domain: str = "general"
    module: str = "general"
    environment: str = "production"
    owner: str = ""
    classification: str = "internal"
    tags: List[str] = field(default_factory=list)
    technology: Optional[str] = None
    language: Optional[str] = None
    version: str = "1.0"

    # Mandatory Tenant Boundary
    tenant: str = "default"

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not isinstance(self.tenant, str) or not self.tenant.strip():
            raise InvalidSchemaError("EnterpriseMetadata.tenant must be a non-empty string isolation boundary.")
        if not isinstance(self.system, str) or not isinstance(self.domain, str):
            raise InvalidSchemaError("EnterpriseMetadata string fields must be valid strings.")

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EnterpriseMetadata:
        if not isinstance(data, dict):
            raise InvalidSchemaError("Input to from_dict must be a dictionary.")
        allowed = set(cls.__dataclass_fields__.keys())
        _check_no_unknown_fields(data, allowed, "EnterpriseMetadata")
        try:
            return cls(**data)
        except (TypeError, ValueError) as e:
            raise InvalidSchemaError(f"Failed to instantiate EnterpriseMetadata: {e}") from e

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> EnterpriseMetadata:
        try:
            return cls.from_dict(json.loads(json_str))
        except json.JSONDecodeError as e:
            raise InvalidSchemaError(f"Invalid JSON format for EnterpriseMetadata: {e}") from e
