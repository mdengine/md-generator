from __future__ import annotations

from md_generator.sap.models.entities.kinds import SapObjectKind
from md_generator.sap.models.entities.sap_object import SapObject
from md_generator.sap.models.metadata.abap import AbapAnalysis, AbapViewReference, ResolutionResult


def _slug(name: str) -> str:
    return name.lower().replace("/", "_").replace(" ", "_")


def _path_for_kind(kind: SapObjectKind, name: str) -> str:
    slug = _slug(name)
    if kind == SapObjectKind.CDS_VIEW:
        return f"cds/views/{slug}.md"
    if kind == SapObjectKind.HANA_CALCULATION_VIEW:
        return f"hana/calculation-views/{slug}.md"
    if kind == SapObjectKind.TABLE:
        return f"ddic/tables/{slug}.md"
    return ""


def _resolve_object(by_name: dict[str, SapObject], name: str, schema: str = "") -> SapObject | None:
    key = name.upper()
    if key in by_name:
        return by_name[key]
    for obj in by_name.values():
        if obj.name.upper() == key:
            return obj
    if schema:
        composite = f"{schema}::{key}"
        for obj in by_name.values():
            if obj.name.upper() == composite or obj.name.upper() == key:
                return obj
    return None


def resolve_view_references(
    refs: list[AbapViewReference],
    by_name: dict[str, SapObject],
) -> list[AbapViewReference]:
    resolved: list[AbapViewReference] = []
    for ref in refs:
        obj = _resolve_object(by_name, ref.name, ref.schema)
        resolution = ref.resolution
        if obj is not None:
            path = _path_for_kind(obj.kind, obj.name)
            resolution = ResolutionResult(
                target=ref.name,
                resolved_stable_id=obj.object_id,
                resolved_path=path,
                confidence=max(ref.confidence, 0.9),
                resolution_strategy="same_run_name_match",
                match_reason=f"Matched {obj.kind.value} '{obj.name}' in run",
            )
        elif not resolution.resolution_strategy or resolution.resolution_strategy == "unresolved":
            resolution = ResolutionResult(
                target=ref.name,
                confidence=ref.confidence,
                resolution_strategy="heuristic_only",
                match_reason=resolution.match_reason or f"Heuristic classification as {ref.kind}",
            )
        resolved.append(
            AbapViewReference(
                name=ref.name,
                schema=ref.schema,
                kind=ref.kind,
                confidence=resolution.confidence,
                source_sql_line=ref.source_sql_line,
                resolution=resolution,
            )
        )
    return resolved


def enrich_abap_objects_in_run(objects: list[SapObject]) -> None:
    """Resolve ABAP view references against all objects in the run; mutates raw_metadata."""
    by_name = {obj.name.upper(): obj for obj in objects}
    for obj in objects:
        if obj.kind != SapObjectKind.PROGRAM or not obj.raw_metadata:
            continue
        abap = obj.raw_metadata.get("abap")
        if not isinstance(abap, dict):
            continue
        refs: list[AbapViewReference] = []
        for r in abap.get("view_references", []) or []:
            if not isinstance(r, dict):
                continue
            res_dict = r.get("resolution") or {}
            refs.append(
                AbapViewReference(
                    name=r.get("name", ""),
                    schema=r.get("schema", ""),
                    kind=r.get("kind", "unknown"),  # type: ignore[arg-type]
                    confidence=float(r.get("confidence", 0.5)),
                    source_sql_line=int(r.get("source_sql_line", 0)),
                    resolution=ResolutionResult(
                        target=res_dict.get("target", r.get("name", "")),
                        resolved_stable_id=res_dict.get("resolved_stable_id", r.get("resolved_stable_id", "")),
                        resolved_path=res_dict.get("resolved_path", r.get("resolved_path", "")),
                        confidence=float(res_dict.get("confidence", r.get("confidence", 0.5))),
                        resolution_strategy=res_dict.get("resolution_strategy", "heuristic"),
                        match_reason=res_dict.get("match_reason", ""),
                    ),
                )
            )
        if refs:
            abap["view_references"] = [r.to_dict() for r in resolve_view_references(refs, by_name)]


def enrich_abap_analysis(analysis: AbapAnalysis, objects: list[SapObject]) -> AbapAnalysis:
    by_name = {obj.name.upper(): obj for obj in objects}
    analysis.view_references = resolve_view_references(analysis.view_references, by_name)
    return analysis
