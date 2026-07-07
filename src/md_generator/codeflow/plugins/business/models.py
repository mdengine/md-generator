from __future__ import annotations

from dataclasses import dataclass, field
from md_generator.codeflow.enterprise_ir.base import BaseEntity


@dataclass
class CapabilityEntity(BaseEntity):
    capability_name: str = ""
    business_domain: str = ""
    associated_code_units: list[str] = field(default_factory=list)  # URIs/IDs of associated files/classes/methods


@dataclass
class BusinessProcess(BaseEntity):
    process_name: str = ""
    steps: list[str] = field(default_factory=list)  # Ordered sequence of method/API URIs representing the flow
    actors: list[str] = field(default_factory=list)  # Users, systems, or triggers initiating this process


@dataclass
class BusinessService(BaseEntity):
    service_name: str = ""
    exposed_apis: list[str] = field(default_factory=list)  # List of ApiEntity/Route URIs
    business_purpose: str = ""


@dataclass
class DomainModel(BaseEntity):
    model_name: str = ""
    fields_attributes: dict[str, str] = field(default_factory=dict)  # Field name -> type/semantic purpose
    relationships: list[str] = field(default_factory=list)  # Relational links to other domain models


@dataclass
class BusinessRule(BaseEntity):
    rule_name: str = ""
    constraint_expression: str = ""
    associated_entities: list[str] = field(default_factory=list)  # Entities governed by this business rule
