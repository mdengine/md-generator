from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from md_generator.codeflow.enterprise_ir.base import BaseEntity


@dataclass
class ConfigEntity(BaseEntity):
    key: str
    value: str
    type_name: str  # number, string, boolean, object, array
    source: str
    line: int | None
    env_var: str | None = None
    profile: str | None = None
    comments: str | None = None
    usage_status: Literal["Unused", "Referenced", "Missing", "Deprecated", "Duplicated"] = "Unused"
