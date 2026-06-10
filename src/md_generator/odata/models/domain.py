from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ODataVersion(str, Enum):
    V1 = "1.0"
    V2 = "2.0"
    V3 = "3.0"
    V4 = "4.0"
    UNKNOWN = "unknown"


class ODataFormat(str, Enum):
    EDMX_XML = "edmx_xml"
    CSDL_JSON = "csdl_json"



class NavMultiplicity(str, Enum):
    ONE = "1"
    MANY = "n"
    ZERO_OR_ONE = "0..1"
    ONE_OR_MANY = "1..n"


def make_stable_id(
    version: ODataVersion,
    namespace: str,
    kind: str,
    name: str,
    *,
    service: str = "",
) -> str:
    ver = version.value.replace(".", "_")
    ns = namespace or "_"
    svc = f":{service}" if service else ""
    return f"odata:v{ver}:{ns}{svc}:{kind}:{name}"


@dataclass(slots=True)
class ODataCapabilities:
    insertable: bool | None = None
    updatable: bool | None = None
    deletable: bool | None = None
    searchable: bool | None = None
    filterable: bool | None = None
    sortable: bool | None = None
    expandable: bool | None = None
    top_supported: bool | None = None
    skip_supported: bool | None = None
    count_supported: bool | None = None
    filter_functions: list[str] = field(default_factory=list)

    def supported_query_options(self, version: ODataVersion) -> list[str]:
        opts: list[str] = []
        if self.filterable is not False:
            opts.append("$filter")
        opts.append("$select")
        if self.expandable is not False:
            opts.append("$expand")
        if self.sortable is not False:
            opts.append("$orderby")
        if self.searchable:
            opts.append("$search")
        if self.top_supported is not False:
            opts.append("$top")
        if self.skip_supported is not False:
            opts.append("$skip")
        if self.count_supported is not False:
            opts.append("$count")
        if version in (ODataVersion.V2, ODataVersion.V3, ODataVersion.V4):
            if "$filter" not in opts:
                opts.insert(0, "$filter")
        return sorted(set(opts))

    def to_dict(self) -> dict[str, Any]:
        return {
            "insertable": self.insertable,
            "updatable": self.updatable,
            "deletable": self.deletable,
            "searchable": self.searchable,
            "filterable": self.filterable,
            "sortable": self.sortable,
            "expandable": self.expandable,
            "top_supported": self.top_supported,
            "skip_supported": self.skip_supported,
            "count_supported": self.count_supported,
            "filter_functions": list(self.filter_functions),
        }


@dataclass(slots=True)
class ODataProperty:
    name: str
    type_name: str = ""
    nullable: bool = True
    stable_id: str = ""


@dataclass(slots=True)
class ODataNavigationProperty:
    name: str
    target_type: str = ""
    partner: str = ""
    multiplicity: str = NavMultiplicity.MANY.value
    stable_id: str = ""


@dataclass(slots=True)
class ODataEntityType:
    name: str
    namespace: str = ""
    properties: list[ODataProperty] = field(default_factory=list)
    navigation_properties: list[ODataNavigationProperty] = field(default_factory=list)
    keys: list[str] = field(default_factory=list)
    annotations: dict[str, str] = field(default_factory=dict)
    stable_id: str = ""


@dataclass(slots=True)
class ODataEntitySet:
    name: str
    entity_type: str = ""
    namespace: str = ""
    capabilities: ODataCapabilities = field(default_factory=ODataCapabilities)
    annotations: dict[str, str] = field(default_factory=dict)
    stable_id: str = ""


@dataclass(slots=True)
class ODataAction:
    name: str
    namespace: str = ""
    is_bound: bool = False
    entity_type: str = ""
    parameters: list[dict[str, str]] = field(default_factory=list)
    return_type: str = ""
    stable_id: str = ""


@dataclass(slots=True)
class ODataFunction:
    name: str
    namespace: str = ""
    is_bound: bool = False
    entity_type: str = ""
    parameters: list[dict[str, str]] = field(default_factory=list)
    return_type: str = ""
    stable_id: str = ""


@dataclass(slots=True)
class ODataComplexType:
    name: str
    namespace: str = ""
    properties: list[ODataProperty] = field(default_factory=list)
    stable_id: str = ""


@dataclass(slots=True)
class ODataEnumType:
    name: str
    namespace: str = ""
    members: list[str] = field(default_factory=list)
    stable_id: str = ""


@dataclass(slots=True)
class ODataMetadataDocument:
    service_name: str
    odata_version: ODataVersion = ODataVersion.UNKNOWN
    odata_format: ODataFormat = ODataFormat.EDMX_XML
    metadata_url: str = ""
    service_root: str = ""
    default_namespace: str = ""
    container_name: str = ""
    entity_types: list[ODataEntityType] = field(default_factory=list)
    entity_sets: list[ODataEntitySet] = field(default_factory=list)
    actions: list[ODataAction] = field(default_factory=list)
    functions: list[ODataFunction] = field(default_factory=list)
    complex_types: list[ODataComplexType] = field(default_factory=list)
    enum_types: list[ODataEnumType] = field(default_factory=list)
    stable_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_name": self.service_name,
            "odata_version": self.odata_version.value,
            "odata_format": self.odata_format.value,
            "metadata_url": self.metadata_url,
            "service_root": self.service_root,
            "default_namespace": self.default_namespace,
            "container_name": self.container_name,
            "stable_id": self.stable_id,
            "entity_types": [
                {
                    "name": e.name,
                    "namespace": e.namespace,
                    "stable_id": e.stable_id,
                    "keys": e.keys,
                    "properties": [{"name": p.name, "type": p.type_name} for p in e.properties],
                    "navigation": [
                        {
                            "name": n.name,
                            "target": n.target_type,
                            "multiplicity": n.multiplicity,
                        }
                        for n in e.navigation_properties
                    ],
                    "annotations": dict(e.annotations),
                }
                for e in self.entity_types
            ],
            "entity_sets": [
                {
                    "name": s.name,
                    "entity_type": s.entity_type,
                    "stable_id": s.stable_id,
                    "capabilities": s.capabilities.to_dict(),
                }
                for s in self.entity_sets
            ],
            "actions": [a.name for a in self.actions],
            "functions": [f.name for f in self.functions],
            "complex_types": [c.name for c in self.complex_types],
            "enum_types": [e.name for e in self.enum_types],
        }
