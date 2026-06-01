"""Operational notes and mapping complexity metrics for Elasticsearch exports."""

from __future__ import annotations

from typing import Any

from md_generator.db.core.elasticsearch_format import flatten_mapping_properties
from md_generator.db.core.elasticsearch_query_classify import (
    HYBRID_SEARCH,
    SEMANTIC_SEARCH,
    VECTOR_SEARCH,
    format_query_type_heading,
)
from md_generator.db.core.models import (
    ElasticsearchDataStreamInfo,
    ElasticsearchIlmPolicyInfo,
    ElasticsearchIndexInfo,
    ElasticsearchSearchTemplateInfo,
    ElasticsearchSlmPolicyInfo,
    ElasticsearchSnapshotRepositoryInfo,
)


def mapping_complexity_metrics(
    properties: dict[str, Any] | None,
    *,
    mappings_root: dict[str, Any] | None = None,
) -> dict[str, Any]:
    props = properties if isinstance(properties, dict) else {}
    rows = flatten_mapping_properties(props) if props else []
    dynamic_mappings: str | bool | None = None
    if isinstance(mappings_root, dict) and "dynamic" in mappings_root:
        dynamic_mappings = mappings_root.get("dynamic")
    elif isinstance(props, dict) and "dynamic" in props:
        dynamic_mappings = props.get("dynamic")

    return {
        "total_fields": len(rows),
        "nested_fields": sum(1 for _, t, _ in rows if t == "nested"),
        "dense_vector_fields": sum(1 for _, t, _ in rows if t == "dense_vector"),
        "sparse_vector_fields": sum(1 for _, t, _ in rows if t == "sparse_vector"),
        "semantic_text_fields": sum(1 for _, t, _ in rows if t == "semantic_text"),
        "dynamic_mappings": dynamic_mappings,
    }


def format_mapping_summary_markdown(metrics: dict[str, Any]) -> str:
    if metrics.get("total_fields", 0) == 0 and metrics.get("dynamic_mappings") is None:
        return ""
    parts = ["## Mapping Summary\n\n"]
    parts.append(f"- **Total fields:** {metrics['total_fields']:,}\n")
    if metrics.get("nested_fields"):
        parts.append(f"- **Nested fields:** {metrics['nested_fields']:,}\n")
    if metrics.get("dense_vector_fields"):
        parts.append(f"- **Dense vector fields:** {metrics['dense_vector_fields']:,}\n")
    if metrics.get("sparse_vector_fields"):
        parts.append(f"- **Sparse vector fields:** {metrics['sparse_vector_fields']:,}\n")
    if metrics.get("semantic_text_fields"):
        parts.append(f"- **Semantic text fields:** {metrics['semantic_text_fields']:,}\n")
    dynamic = metrics.get("dynamic_mappings")
    if dynamic is not None:
        parts.append(f"- **Dynamic mappings:** `{dynamic}`\n")
    parts.append("\n")
    return "".join(parts)


def format_operational_notes_markdown(notes: list[str]) -> str:
    if not notes:
        return ""
    parts = ["## Operational Notes\n\n"]
    for note in notes:
        parts.append(f"- {note}\n")
    parts.append("\n")
    return "".join(parts)


def operational_notes_for_index(
    idx: ElasticsearchIndexInfo,
    metrics: dict[str, Any] | None = None,
) -> list[str]:
    notes: list[str] = []
    health = (idx.health or "").lower()
    if health in ("yellow", "red"):
        notes.append(f"Cluster health for this index is `{idx.health}`")
    if idx.replica_shards == 0:
        notes.append("No replica shards configured (`number_of_replicas=0`)")
    metrics = metrics or {}
    dense = int(metrics.get("dense_vector_fields") or 0)
    sparse = int(metrics.get("sparse_vector_fields") or 0)
    semantic = int(metrics.get("semantic_text_fields") or 0)
    vector_total = dense + sparse + semantic
    if dense:
        notes.append(
            f"Uses dense_vector fields for semantic retrieval ({dense} field{'s' if dense != 1 else ''})"
        )
    if sparse:
        notes.append(f"Contains {sparse} sparse_vector field{'s' if sparse != 1 else ''}")
    if semantic:
        notes.append(f"Contains {semantic} semantic_text field{'s' if semantic != 1 else ''}")
    if vector_total and not (dense or sparse or semantic):
        notes.append("Index contains vector-capable field mappings")
    return notes


def operational_notes_for_snapshot(repo: ElasticsearchSnapshotRepositoryInfo) -> list[str]:
    notes: list[str] = []
    if repo.operational.get("readonly") is True:
        notes.append("Repository is read-only")
    if repo.operational.get("compress") is True:
        notes.append("Snapshot compression is enabled")
    if repo.notes and "slm" in repo.notes.lower():
        notes.append("Referenced by SLM snapshot policies")
    return notes


def _walk_policy_actions(policy: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    phases = policy.get("phases")
    if not isinstance(phases, dict):
        return notes
    for phase_name in sorted(phases.keys()):
        phase = phases.get(phase_name)
        if not isinstance(phase, dict):
            continue
        if phase_name in ("cold", "frozen"):
            notes.append(f"Policy references `{phase_name}` tier storage")
        actions = phase.get("actions")
        if not isinstance(actions, dict):
            continue
        if "delete" in actions:
            notes.append("Delete action configured")
        if "searchable_snapshot" in actions or "snapshot" in actions:
            notes.append("Snapshot action configured")
    return notes


def operational_notes_for_ilm(pol: ElasticsearchIlmPolicyInfo) -> list[str]:
    return _walk_policy_actions(pol.policy if isinstance(pol.policy, dict) else {})


def operational_notes_for_slm(pol: ElasticsearchSlmPolicyInfo) -> list[str]:
    notes: list[str] = []
    if pol.schedule:
        notes.append(f"Scheduled snapshots: `{pol.schedule}`")
    if pol.repository:
        notes.append(f"Target repository: `{pol.repository}`")
    body = pol.policy if isinstance(pol.policy, dict) else {}
    retention = body.get("retention")
    if isinstance(retention, dict) and retention.get("expire_after"):
        notes.append(f"Retention expire_after: `{retention['expire_after']}`")
    return notes


def operational_notes_for_search_template(tpl: ElasticsearchSearchTemplateInfo) -> list[str]:
    notes: list[str] = []
    if not tpl.query_types:
        return notes
    label = format_query_type_heading(tpl.query_types)
    if HYBRID_SEARCH in tpl.query_types:
        notes.append(f"Hybrid lexical + vector search detected ({label})")
    elif VECTOR_SEARCH in tpl.query_types:
        notes.append("Vector search template (knn / dense_vector usage)")
    elif SEMANTIC_SEARCH in tpl.query_types:
        notes.append("Semantic search template detected")
    elif label and "unavailable" not in label.lower():
        notes.append(f"Query classification: {label}")
    return notes


def operational_notes_for_data_stream(ds: ElasticsearchDataStreamInfo) -> list[str]:
    notes: list[str] = []
    if ds.generation is not None:
        notes.append(f"Data stream generation: {ds.generation}")
    if ds.indices:
        notes.append(f"{len(ds.indices)} backing index/indices")
    if ds.template:
        notes.append(f"Managed by index template `{ds.template}`")
    return notes
