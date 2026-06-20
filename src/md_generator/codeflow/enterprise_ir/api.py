from __future__ import annotations

from dataclasses import dataclass

from md_generator.codeflow.enterprise_ir.base import BaseEntity


@dataclass
class ApiEntity(BaseEntity):
    route_path: str
    http_method: str  # GET, POST, PUT, DELETE, etc.
    controller_class: str | None = None
    controller_method: str | None = None
    request_payload_type: str | None = None
    response_payload_type: str | None = None
