from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.graph.model import ArtifactGraph
from md_generator.sap.models.entities.sap_object import SapObject


_CANONICAL_MODELS: dict[str, type[BaseModel]] = {}


def register_canonical_model(artifact_type: str, model: type[BaseModel]) -> None:
    _CANONICAL_MODELS[artifact_type] = model


def _ensure_registry() -> None:
    if _CANONICAL_MODELS:
        return
    from md_generator.sap.canonical.bw.adso import BwAdso
    from md_generator.sap.canonical.bw.composite_provider import BwCompositeProvider
    from md_generator.sap.canonical.bw.dtp import BwDtp
    from md_generator.sap.canonical.bw.info_object import BwInfoObject
    from md_generator.sap.canonical.bw.transformation import BwTransformation
    from md_generator.sap.canonical.datasphere.analytical_model import DatasphereAnalyticalModel
    from md_generator.sap.canonical.datasphere.data_flow import DatasphereDataFlow
    from md_generator.sap.canonical.datasphere.view import DatasphereView
    from md_generator.sap.canonical.hana.calculation_view import CalculationView

    models = [
        ("hana.calculation_view", CalculationView),
        ("bw.adso", BwAdso),
        ("bw.composite_provider", BwCompositeProvider),
        ("bw.transformation", BwTransformation),
        ("bw.dtp", BwDtp),
        ("bw.info_object", BwInfoObject),
        ("datasphere.analytical_model", DatasphereAnalyticalModel),
        ("datasphere.view", DatasphereView),
        ("datasphere.data_flow", DatasphereDataFlow),
    ]
    for t, m in models:
        register_canonical_model(t, m)
    for t in (
        "hana.analytic_view",
        "hana.attribute_view",
        "hana.hdi_calculation_view",
        "hana.sql_view",
        "external.dbt.model",
        "external.snowflake.relation",
        "external.kafka.topic",
        "external.informatica.mapping",
    ):
        register_canonical_model(t, CanonicalArtifact)


def load_canonical(data: dict[str, Any]) -> CanonicalArtifact:
    _ensure_registry()
    artifact_type = data.get("artifact_type", "")
    model = _CANONICAL_MODELS.get(artifact_type, CanonicalArtifact)
    return model.model_validate(data)  # type: ignore[return-value]


def canonical_from_object(
    obj: SapObject,
    normalizer: object,
) -> tuple[CanonicalArtifact | None, ArtifactGraph]:
    if obj.raw_metadata and obj.raw_metadata.get("canonical"):
        data = obj.raw_metadata["canonical"]
        try:
            artifact = load_canonical(data)
            frag_data = obj.raw_metadata.get("graph_fragment") or {}
            frag = ArtifactGraph.model_validate(frag_data) if frag_data else ArtifactGraph(
                graph_id=getattr(artifact.identity, "stable_id", obj.object_id)
            )
            return artifact, frag
        except Exception:
            pass
    return normalizer.normalize(obj)  # type: ignore[no-any-return]
