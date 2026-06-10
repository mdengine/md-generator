from __future__ import annotations

import re

from md_generator.sap.models.metadata.cds import CdsStructuredType, CdsTypeComponent
from md_generator.sap.parser.cds.ddl_common import (
    end_user_label,
    extract_braced_body,
    parse_annotations,
)

_RE_DEFINE_TYPE = re.compile(r"define\s+type\s+(\w+)", re.I)
_RE_ENHANCEMENT = re.compile(
    r"@AbapCatalog\.enhancementCategory\s*:\s*#(\w+)",
    re.I,
)
_RE_COMPONENT = re.compile(
    r"^\s*([\w/]+)\s*:\s*([\w/]+)\s*;",
    re.I | re.M,
)


def is_cds_type_ddl(source: str) -> bool:
    return bool(_RE_DEFINE_TYPE.search(source))


def _classify_type(type_name: str) -> str:
    t = type_name.upper().split("/")[-1]
    if t.startswith("SY") and len(t) <= 12:
        return "builtin"
    if "_s_" in t.lower() or (t.startswith("BAL_") and "_S_" in t):
        return "structure"
    if len(t) <= 30 and t.replace("_", "").isalnum():
        if t.endswith("_S_MSG") or t.endswith("_S_CONT") or t.endswith("_S_PARM"):
            return "structure"
    return "type"


def parse_cds_type_ddl(source: str, fallback_name: str) -> CdsStructuredType:
    name = fallback_name.upper()
    m = _RE_DEFINE_TYPE.search(source)
    if m:
        name = m.group(1).upper()

    annotations = parse_annotations(source)
    enhancement = ""
    em = _RE_ENHANCEMENT.search(source)
    if em:
        enhancement = em.group(1).upper()
    elif "AbapCatalog.enhancementCategory" in annotations:
        enhancement = annotations["AbapCatalog.enhancementCategory"].upper()

    body = extract_braced_body(source)
    components: list[CdsTypeComponent] = []
    for cm in _RE_COMPONENT.finditer(body):
        cname = cm.group(1).split("/")[-1].upper()
        ctype = cm.group(2).split("/")[-1].upper()
        components.append(
            CdsTypeComponent(
                name=cname,
                type_name=ctype,
                type_kind=_classify_type(ctype),
            )
        )

    return CdsStructuredType(
        name=name,
        description=end_user_label(annotations),
        enhancement_category=enhancement,
        annotations=annotations,
        components=components,
        definition_source="cds_ddl",
    )
