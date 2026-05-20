from __future__ import annotations

import re
from pathlib import Path

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.models.metadata.cds import CdsAnalysis, CdsAssociation
from md_generator.sap.analyzer.semantics.entity_mapper import infer_semantic_entity
from md_generator.sap.parser.base import ParseContext, SapParseResult

_CDS_SUFFIXES = {".ddls", ".cds", ".ddlx"}
_RE_DEFINE = re.compile(r"define\s+(?:root\s+)?view\s+(\w+)", re.I)
_RE_ENTITY = re.compile(r"entity\s+(\w+)", re.I)
_RE_ASSOC = re.compile(
    r"(association|composition)\s+(?:\[[^\]]*\]\s+)?to\s+(\w+)\s+as\s+(\w+)",
    re.I,
)
_RE_ANNOTATION = re.compile(r"@(\w+(?:\.\w+)*)\s*:\s*['\"]?([^'\"\n]+)", re.I)
_RE_JOIN = re.compile(r"\bjoin\s+([\w.]+)", re.I)


class CdsParserPlugin:
    name = "cds"

    def can_parse(self, path: Path) -> bool:
        return path.suffix.lower() in _CDS_SUFFIXES

    def parse(self, path: Path, ctx: ParseContext) -> SapParseResult:
        source = path.read_text(encoding="utf-8", errors="replace")
        analysis = parse_cds_source(source, path.stem)
        obj = SapObject(
            kind=SapObjectKind.CDS_VIEW,
            name=analysis.view_name,
            package=ctx.package_hint,
            source_path=path,
            raw_metadata={"cds": analysis.to_dict()},
            semantic_entity=analysis.semantic_entity,
            tags=["cds"] + analysis.semantic_tags,
        )
        return SapParseResult(path=path, objects=[obj], metadata={"cds": analysis.to_dict()})


def parse_cds_source(source: str, fallback_name: str) -> CdsAnalysis:
    view_name = fallback_name.upper()
    m = _RE_DEFINE.search(source)
    if m:
        view_name = m.group(1).upper()

    analysis = CdsAnalysis(view_name=view_name)
    for em in _RE_ENTITY.finditer(source):
        analysis.entities.append(em.group(1))
    for jm in _RE_JOIN.finditer(source):
        analysis.joins.append(jm.group(1))
    for am in _RE_ASSOC.finditer(source):
        kind = am.group(1).lower()
        target = am.group(2)
        alias = am.group(3)
        analysis.associations.append(
            CdsAssociation(name=alias, target=target, kind=kind)
        )
        if kind == "composition":
            analysis.compositions.append(alias)
    for ann in _RE_ANNOTATION.finditer(source):
        key = ann.group(1)
        analysis.annotations[key] = ann.group(2).strip()
        if "semantics" in key.lower() or "objectmodel" in key.lower():
            analysis.semantic_tags.append(f"{key}={ann.group(2).strip()}")

    analysis.semantic_entity = infer_semantic_entity(view_name, analysis.annotations)
    return analysis
