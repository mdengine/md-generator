from __future__ import annotations

from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.markdown.builders.renderer_context import RendererContext
from md_generator.sap.markdown.cross_link_registry import CrossLinkRegistry
from md_generator.sap.markdown.relationship_weights import relationship_weight
from md_generator.sap.markdown.resolved_link import ResolvedLink


def format_semantic_narrative(artifact: CanonicalArtifact, ctx: RendererContext | None) -> str:
    reg: CrossLinkRegistry | None = getattr(ctx, "cross_link_registry", None) if ctx else None
    if reg is None:
        return ""

    lines: list[str] = ["## Semantic summary", ""]
    stable_id = artifact.identity.stable_id
    neighbors = reg.neighbors_for_render(stable_id) if stable_id else []
    if neighbors:
        lines.append("### Relationship summary")
        lines.append("")
        primary: list[str] = []
        secondary: list[str] = []
        for node, edge in neighbors[:20]:
            link = reg.resolve_link("", node.label)
            link.stable_id = link.stable_id or node.node_id
            link.importance_score = reg.get_importance_score(link.stable_id)
            rel_w = relationship_weight(edge.relationship)
            entry = f"- `{node.label}` ({edge.relationship.value}, weight {rel_w:.2f})"
            if link.strategy != "unresolved":
                entry += f" — resolved via `{link.strategy}` (confidence {link.confidence:.2f})"
            elif link.confidence < 0.6:
                entry += " — _low confidence_"
            if link.importance_score > 0:
                entry += f" — **[importance: {link.importance_score:.1f}]**"
            (primary if rel_w >= 0.65 else secondary).append(entry)
        if primary:
            lines.extend(["**Primary relationships**", ""] + primary + [""])
        if secondary:
            lines.extend(["**Secondary relationships**", ""] + secondary + [""])
    else:
        lines.append("_No graph neighbors in this run._")
        lines.append("")

    de_meta = artifact.metadata.get("data_element") or {}
    if de_meta.get("type_name"):
        chain = reg.related_ddic_chain(artifact.name)
        lines.extend(["### DDIC resolution chain", ""])
        for link in chain:
            lines.append(_format_chain_link(link))
        lines.append("")

    usage = _usage_counts(reg, stable_id)
    if usage:
        lines.extend(["### Usage analytics", ""] + [f"- {line}" for line in usage] + [""])

    meaning = _business_meaning(artifact)
    if meaning:
        lines.extend(["### Business meaning", "", meaning, ""])

    return "\n".join(lines).rstrip() + "\n"


def _format_chain_link(link: ResolvedLink) -> str:
    href = f" → [{link.href}]({link.href})" if link.href else ""
    badge = f" — **[importance: {link.importance_score:.1f}]**" if link.importance_score > 0 else ""
    return (
        f"- `{link.target}` via `{link.strategy}` "
        f"(confidence {link.confidence:.2f}){href}{badge}"
    )


def _usage_counts(reg: CrossLinkRegistry, stable_id: str) -> list[str]:
    if not reg.graph_store or not stable_id:
        return []
    downstream = reg.graph_store.downstream(stable_id)
    if not downstream:
        return []
    return [f"Referenced by {len(downstream)} downstream artifact(s)"]


def _business_meaning(artifact: CanonicalArtifact) -> str:
    meta = artifact.metadata
    de = meta.get("data_element") or {}
    dom = meta.get("domain") or {}
    st = meta.get("structure") or meta.get("cds_structure") or {}
    labels = [
        de.get("long_field_label"),
        de.get("medium_field_label"),
        de.get("short_field_label"),
        dom.get("description"),
        st.get("description"),
        artifact.metadata.get("description"),
    ]
    for label in labels:
        if label:
            return f"{artifact.name} represents **{label}** in the SAP dictionary."
    if artifact.identity.semantic_entity:
        return f"{artifact.name} is classified as **{artifact.identity.semantic_entity}**."
    return ""
