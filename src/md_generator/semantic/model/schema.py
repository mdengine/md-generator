from __future__ import annotations

"""Canonical Schema-Versioned Data Models for md_generator semantic layer.

Phase 0A Implementation: Framework-neutral domain contracts, schema validation,
and deterministic canonical serialization.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set
import json
import re

SCHEMA_VERSION = "1.0"
HEX_64_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
HEX_ANY_PATTERN = re.compile(r"^[0-9a-fA-F]+$")


class InvalidSchemaError(ValueError):
    """Raised when a canonical semantic model fails schema validation."""
    pass


def _validate_hex_id(value: str, field_name: str, exact_length: bool = True) -> None:
    if not isinstance(value, str) or not value:
        raise InvalidSchemaError(f"{field_name} must be a non-empty string.")
    pattern = HEX_64_PATTERN if exact_length else HEX_ANY_PATTERN
    if not pattern.fullmatch(value):
        expected_desc = "64-character hex SHA-256 string" if exact_length else "hexadecimal string"
        raise InvalidSchemaError(f"{field_name} must be a valid {expected_desc}. Got: '{value}'")


def _check_no_unknown_fields(data: Dict[str, Any], allowed_fields: Set[str], model_name: str) -> None:
    unknown = set(data.keys()) - allowed_fields
    if unknown:
        raise InvalidSchemaError(f"Unknown fields for {model_name}: {sorted(list(unknown))}")


# Domain location rules: allowed domain-specific fields per location_type
LOCATION_DOMAIN_FIELDS: Dict[str, Set[str]] = {
    "pdf": {"page"},
    "docx": {"section"},
    "pptx": {"slide"},
    "xlsx": {"sheet", "cell"},
    "code": {"line_start", "line_end", "column_start", "column_end", "symbol"},
    "openapi": {"endpoint", "http_method"},
    "database": {"table", "column_name"},
    "sap": {"sap_object"},
    "log": {"timestamp", "trace_id"},
    "otel": {"timestamp", "trace_id"},
    "generic": set(),
}

VALID_LOCATION_TYPES: Set[str] = set(LOCATION_DOMAIN_FIELDS.keys())


@dataclass
class SourceLocation:
    location_type: str = "generic"
    uri: str = ""
    path: str = ""
    page: Optional[int] = None
    section: Optional[str] = None
    slide: Optional[int] = None
    sheet: Optional[str] = None
    cell: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    symbol: Optional[str] = None
    endpoint: Optional[str] = None
    http_method: Optional[str] = None
    table: Optional[str] = None
    column_name: Optional[str] = None
    sap_object: Optional[str] = None
    timestamp: Optional[str] = None
    trace_id: Optional[str] = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if self.location_type not in VALID_LOCATION_TYPES:
            raise InvalidSchemaError(
                f"Invalid location_type: '{self.location_type}'. Must be one of {sorted(list(VALID_LOCATION_TYPES))}"
            )

        # Enforce that domain fields outside the allowed set for this location_type are None
        allowed_domain_fields = LOCATION_DOMAIN_FIELDS[self.location_type]
        all_domain_fields = set().union(*LOCATION_DOMAIN_FIELDS.values())
        disallowed_fields = all_domain_fields - allowed_domain_fields

        for field_name in disallowed_fields:
            if getattr(self, field_name) is not None:
                raise InvalidSchemaError(
                    f"Field '{field_name}' is not permitted for location_type '{self.location_type}'."
                )

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SourceLocation:
        if not isinstance(data, dict):
            raise InvalidSchemaError("Input to from_dict must be a dictionary.")
        allowed = set(cls.__dataclass_fields__.keys())
        _check_no_unknown_fields(data, allowed, "SourceLocation")
        try:
            return cls(**data)
        except (TypeError, ValueError) as e:
            raise InvalidSchemaError(f"Failed to instantiate SourceLocation: {e}") from e


@dataclass
class Entity:
    entity_id: str
    entity_type: str
    name: str
    qualified_name: str
    location: Optional[SourceLocation] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        _validate_hex_id(self.entity_id, "Entity.entity_id", exact_length=False)
        if not self.entity_type or not isinstance(self.entity_type, str):
            raise InvalidSchemaError("Entity.entity_type must be a non-empty string.")
        if not self.name or not isinstance(self.name, str):
            raise InvalidSchemaError("Entity.name must be a non-empty string.")
        if not self.qualified_name or not isinstance(self.qualified_name, str):
            raise InvalidSchemaError("Entity.qualified_name must be a non-empty string.")
        if self.location:
            self.location.validate()

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.location:
            d["location"] = self.location.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Entity:
        if not isinstance(data, dict):
            raise InvalidSchemaError("Input to from_dict must be a dictionary.")
        allowed = set(cls.__dataclass_fields__.keys())
        _check_no_unknown_fields(data, allowed, "Entity")
        data_copy = dict(data)
        if "location" in data_copy and data_copy["location"] is not None:
            if isinstance(data_copy["location"], dict):
                data_copy["location"] = SourceLocation.from_dict(data_copy["location"])
        try:
            return cls(**data_copy)
        except (TypeError, ValueError) as e:
            raise InvalidSchemaError(f"Failed to instantiate Entity: {e}") from e


@dataclass
class Relationship:
    relationship_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    confidence: float = 1.0
    provenance: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        _validate_hex_id(self.relationship_id, "Relationship.relationship_id", exact_length=False)
        _validate_hex_id(self.source_entity_id, "Relationship.source_entity_id", exact_length=False)
        _validate_hex_id(self.target_entity_id, "Relationship.target_entity_id", exact_length=False)
        if not self.relationship_type or not isinstance(self.relationship_type, str):
            raise InvalidSchemaError("Relationship.relationship_type must be a non-empty string.")
        if not isinstance(self.confidence, (int, float)) or not (0.0 <= self.confidence <= 1.0):
            raise InvalidSchemaError("Relationship.confidence must be a float between 0.0 and 1.0.")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Relationship:
        if not isinstance(data, dict):
            raise InvalidSchemaError("Input to from_dict must be a dictionary.")
        allowed = set(cls.__dataclass_fields__.keys())
        _check_no_unknown_fields(data, allowed, "Relationship")
        try:
            return cls(**data)
        except (TypeError, ValueError) as e:
            raise InvalidSchemaError(f"Failed to instantiate Relationship: {e}") from e


@dataclass
class CanonicalMetadata:
    system: str = "default"
    domain: str = "general"
    module: str = "general"
    source_type: str = "generic"
    source_uri: str = ""
    source_path: str = ""
    repository: Optional[str] = None
    commit: Optional[str] = None
    branch: Optional[str] = None
    language: Optional[str] = None
    api_method: Optional[str] = None
    api_path: Optional[str] = None
    table_name: Optional[str] = None
    symbol_name: Optional[str] = None
    trace_id: Optional[str] = None
    security_classification: str = "internal"

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not isinstance(self.system, str) or not isinstance(self.domain, str):
            raise InvalidSchemaError("Metadata string fields must be valid strings.")

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CanonicalMetadata:
        if not isinstance(data, dict):
            raise InvalidSchemaError("Input to from_dict must be a dictionary.")
        allowed = set(cls.__dataclass_fields__.keys())
        _check_no_unknown_fields(data, allowed, "CanonicalMetadata")
        try:
            return cls(**data)
        except (TypeError, ValueError) as e:
            raise InvalidSchemaError(f"Failed to instantiate CanonicalMetadata: {e}") from e


@dataclass
class DocumentLineage:
    source_hash: str = ""
    parent_document_id: Optional[str] = None
    extractor_name: str = ""
    extractor_version: str = "1.0"
    created_timestamp: float = 0.0

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if self.parent_document_id:
            _validate_hex_id(self.parent_document_id, "DocumentLineage.parent_document_id", exact_length=False)

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DocumentLineage:
        if not isinstance(data, dict):
            raise InvalidSchemaError("Input to from_dict must be a dictionary.")
        allowed = set(cls.__dataclass_fields__.keys())
        _check_no_unknown_fields(data, allowed, "DocumentLineage")
        try:
            return cls(**data)
        except (TypeError, ValueError) as e:
            raise InvalidSchemaError(f"Failed to instantiate DocumentLineage: {e}") from e


@dataclass
class ChunkLineage:
    source_hash: str = ""
    chunk_hash: str = ""
    parent_chunk_id: Optional[str] = None
    sequence_index: int = 0
    location: Optional[SourceLocation] = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if self.parent_chunk_id:
            _validate_hex_id(self.parent_chunk_id, "ChunkLineage.parent_chunk_id", exact_length=False)
        if self.location:
            self.location.validate()

    def to_dict(self) -> Dict[str, Any]:
        d = {k: v for k, v in asdict(self).items() if v is not None}
        if self.location:
            d["location"] = self.location.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChunkLineage:
        if not isinstance(data, dict):
            raise InvalidSchemaError("Input to from_dict must be a dictionary.")
        allowed = set(cls.__dataclass_fields__.keys())
        _check_no_unknown_fields(data, allowed, "ChunkLineage")
        data_copy = dict(data)
        if "location" in data_copy and data_copy["location"] is not None:
            if isinstance(data_copy["location"], dict):
                data_copy["location"] = SourceLocation.from_dict(data_copy["location"])
        try:
            return cls(**data_copy)
        except (TypeError, ValueError) as e:
            raise InvalidSchemaError(f"Failed to instantiate ChunkLineage: {e}") from e


@dataclass
class SecurityMetadata:
    is_sanitized: bool = True
    secrets_redacted_count: int = 0
    pii_masked_count: int = 0
    applied_rules: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not isinstance(self.is_sanitized, bool):
            raise InvalidSchemaError("SecurityMetadata.is_sanitized must be a boolean.")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SecurityMetadata:
        if not isinstance(data, dict):
            raise InvalidSchemaError("Input to from_dict must be a dictionary.")
        allowed = set(cls.__dataclass_fields__.keys())
        _check_no_unknown_fields(data, allowed, "SecurityMetadata")
        try:
            return cls(**data)
        except (TypeError, ValueError) as e:
            raise InvalidSchemaError(f"Failed to instantiate SecurityMetadata: {e}") from e


@dataclass
class SemanticDocument:
    schema_version: str = SCHEMA_VERSION
    document_id: str = ""
    sanitized_content: str = ""
    document_type: str = "generic"
    metadata: Optional[CanonicalMetadata] = None
    entities: List[Entity] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    lineage: Optional[DocumentLineage] = None
    security: Optional[SecurityMetadata] = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise InvalidSchemaError(
                f"Unsupported schema_version: '{self.schema_version}'. Expected '{SCHEMA_VERSION}'."
            )
        _validate_hex_id(self.document_id, "SemanticDocument.document_id", exact_length=True)
        if self.metadata:
            self.metadata.validate()
        for e in self.entities:
            e.validate()
        for r in self.relationships:
            r.validate()
        if self.lineage:
            self.lineage.validate()
        if self.security:
            self.security.validate()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "document_id": self.document_id,
            "sanitized_content": self.sanitized_content,
            "document_type": self.document_type,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "entities": [e.to_dict() for e in self.entities],
            "relationships": [r.to_dict() for r in self.relationships],
            "lineage": self.lineage.to_dict() if self.lineage else None,
            "security": self.security.to_dict() if self.security else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SemanticDocument:
        if not isinstance(data, dict):
            raise InvalidSchemaError("Input to from_dict must be a dictionary.")
        allowed = set(cls.__dataclass_fields__.keys())
        _check_no_unknown_fields(data, allowed, "SemanticDocument")

        try:
            metadata = CanonicalMetadata.from_dict(data["metadata"]) if data.get("metadata") else None
            entities = [Entity.from_dict(e) for e in data.get("entities", [])]
            relationships = [Relationship.from_dict(r) for r in data.get("relationships", [])]
            lineage = DocumentLineage.from_dict(data["lineage"]) if data.get("lineage") else None
            security = SecurityMetadata.from_dict(data["security"]) if data.get("security") else None

            doc = cls(
                schema_version=data.get("schema_version", SCHEMA_VERSION),
                document_id=data.get("document_id", ""),
                sanitized_content=data.get("sanitized_content", ""),
                document_type=data.get("document_type", "generic"),
                metadata=metadata,
                entities=entities,
                relationships=relationships,
                lineage=lineage,
                security=security,
            )
            return doc
        except InvalidSchemaError:
            raise
        except (TypeError, ValueError) as e:
            raise InvalidSchemaError(f"Failed to deserialize SemanticDocument: {e}") from e

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> SemanticDocument:
        try:
            return cls.from_dict(json.loads(json_str))
        except json.JSONDecodeError as e:
            raise InvalidSchemaError(f"Invalid JSON format for SemanticDocument: {e}") from e


@dataclass
class SemanticChunk:
    schema_version: str = SCHEMA_VERSION
    chunk_id: str = ""
    document_id: str = ""
    sanitized_content: str = ""
    metadata: Optional[CanonicalMetadata] = None
    entities: List[Entity] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    lineage: Optional[ChunkLineage] = None
    security: Optional[SecurityMetadata] = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise InvalidSchemaError(
                f"Unsupported schema_version: '{self.schema_version}'. Expected '{SCHEMA_VERSION}'."
            )
        _validate_hex_id(self.chunk_id, "SemanticChunk.chunk_id", exact_length=True)
        _validate_hex_id(self.document_id, "SemanticChunk.document_id", exact_length=True)
        if self.metadata:
            self.metadata.validate()
        for e in self.entities:
            e.validate()
        for r in self.relationships:
            r.validate()
        if self.lineage:
            self.lineage.validate()
        if self.security:
            self.security.validate()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "sanitized_content": self.sanitized_content,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "entities": [e.to_dict() for e in self.entities],
            "relationships": [r.to_dict() for r in self.relationships],
            "lineage": self.lineage.to_dict() if self.lineage else None,
            "security": self.security.to_dict() if self.security else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SemanticChunk:
        if not isinstance(data, dict):
            raise InvalidSchemaError("Input to from_dict must be a dictionary.")
        allowed = set(cls.__dataclass_fields__.keys())
        _check_no_unknown_fields(data, allowed, "SemanticChunk")

        try:
            metadata = CanonicalMetadata.from_dict(data["metadata"]) if data.get("metadata") else None
            entities = [Entity.from_dict(e) for e in data.get("entities", [])]
            relationships = [Relationship.from_dict(r) for r in data.get("relationships", [])]
            lineage = ChunkLineage.from_dict(data["lineage"]) if data.get("lineage") else None
            security = SecurityMetadata.from_dict(data["security"]) if data.get("security") else None

            chunk = cls(
                schema_version=data.get("schema_version", SCHEMA_VERSION),
                chunk_id=data.get("chunk_id", ""),
                document_id=data.get("document_id", ""),
                sanitized_content=data.get("sanitized_content", ""),
                metadata=metadata,
                entities=entities,
                relationships=relationships,
                lineage=lineage,
                security=security,
            )
            return chunk
        except InvalidSchemaError:
            raise
        except (TypeError, ValueError) as e:
            raise InvalidSchemaError(f"Failed to deserialize SemanticChunk: {e}") from e

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> SemanticChunk:
        try:
            return cls.from_dict(json.loads(json_str))
        except json.JSONDecodeError as e:
            raise InvalidSchemaError(f"Invalid JSON format for SemanticChunk: {e}") from e
