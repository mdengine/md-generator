from md_generator.sap.canonical.identity import ArtifactIdentity
from md_generator.sap.graph.store import ArtifactGraphStore
from md_generator.sap.index.semantic_entity_registry import SemanticEntityRegistry
from md_generator.sap.lineage.cross_system import link_cross_system_lineage


def test_cross_system_same_as_edges():
    store = ArtifactGraphStore()
    registry = SemanticEntityRegistry()
    registry.register(
        ArtifactIdentity(
            stable_id="HANA::SALES::CV_SALES",
            physical_id="CV_SALES",
            semantic_id="entity:sales_order",
            namespace="HANA::",
        )
    )
    registry.register(
        ArtifactIdentity(
            stable_id="CDS::ZI_SALES",
            physical_id="ZI_SALES",
            semantic_id="entity:sales_order",
            namespace="CDS::",
        )
    )
    linked = link_cross_system_lineage(store, registry)
    assert linked == 1
    same_as = [e for e in store.graph.edges.values() if e.relationship.value == "SAME_AS"]
    assert len(same_as) == 1
    assert same_as[0].properties.get("confidence_score") == 1.0
