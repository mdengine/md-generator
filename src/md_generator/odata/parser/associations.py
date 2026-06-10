from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass

from md_generator.odata.parser import namespaces as ns


@dataclass
class AssociationEnd:
    role: str
    entity_type: str
    multiplicity: str


@dataclass
class AssociationInfo:
    name: str
    namespace: str
    ends: list[AssociationEnd]


class AssociationIndex:
    def __init__(self) -> None:
        self._by_fqn: dict[str, AssociationInfo] = {}

    def add(self, namespace: str, assoc_elem: ET.Element) -> None:
        name = assoc_elem.get("Name") or ""
        ends: list[AssociationEnd] = []
        for end in ns.find_children(assoc_elem, "End"):
            ends.append(
                AssociationEnd(
                    role=end.get("Role") or "",
                    entity_type=end.get("Type") or "",
                    multiplicity=end.get("Multiplicity") or "*",
                )
            )
        fqn = f"{namespace}.{name}" if namespace else name
        self._by_fqn[fqn] = AssociationInfo(name=name, namespace=namespace, ends=ends)

    def resolve_nav_target(
        self,
        relationship: str,
        to_role: str,
    ) -> tuple[str, str]:
        info = self._by_fqn.get(relationship)
        if not info:
            for k, v in self._by_fqn.items():
                if k.endswith(f".{relationship}") or v.name == relationship:
                    info = v
                    break
        if not info:
            return "", "n"
        for end in info.ends:
            if end.role == to_role:
                mult = "n" if end.multiplicity in ("*", "1..*") else "1"
                return end.entity_type.split(".")[-1], mult
        if info.ends:
            end = info.ends[-1]
            mult = "n" if end.multiplicity in ("*", "1..*") else "1"
            return end.entity_type.split(".")[-1], mult
        return "", "n"

    @staticmethod
    def multiplicity_from_type(type_name: str) -> str:
        if type_name.startswith("Collection("):
            return "n"
        return "1"
