from __future__ import annotations

from md_generator.sap.graph.store import ArtifactGraphStore
from md_generator.sap.graph.model import GraphNode, GraphEdge
from md_generator.sap.graph.taxonomy import RelationshipType
from md_generator.sap.markdown.cross_link_registry import CrossLinkRegistry, build_cross_link_registry
from md_generator.sap.markdown.resolved_link import ResolvedLink


def test_multi_hop_bfs_graph_walk():
    # 1. Instantiate the graph store and build nodes
    store = ArtifactGraphStore()

    # Node IDs
    de_id = "DDIC::DE:DE_CHAR100"
    dom_id = "DDIC::DOM:DOM_CHAR100"
    tab_id = "DDIC::T005"
    cds_id = "CDS::ZI_CUSTOMER"
    odata_id = "ODATA::CustomerSet"

    # Add GraphNodes
    store.add_node(GraphNode(node_id=de_id, node_kind="dataset", label="DE_CHAR100", namespace="DDIC::"))
    store.add_node(GraphNode(node_id=dom_id, node_kind="dataset", label="DOM_CHAR100", namespace="DDIC::"))
    store.add_node(GraphNode(node_id=tab_id, node_kind="dataset", label="T005", namespace="DDIC::"))
    store.add_node(GraphNode(node_id=cds_id, node_kind="artifact", label="ZI_CUSTOMER", namespace="CDS::", artifact_type="cds.view"))
    store.add_node(GraphNode(node_id=odata_id, node_kind="artifact", label="CustomerSet", namespace="ODATA::", artifact_type="odata.entity_set"))

    # Add GraphEdges representing multi-hop dependency path
    # DE_CHAR100 --REFERENCES--> DOM_CHAR100
    store.add_edge(GraphEdge(
        edge_id="de_to_dom",
        source_id=de_id,
        target_id=dom_id,
        relationship=RelationshipType.REFERENCES
    ))
    # DOM_CHAR100 --REFERENCES--> T005
    store.add_edge(GraphEdge(
        edge_id="dom_to_tab",
        source_id=dom_id,
        target_id=tab_id,
        relationship=RelationshipType.REFERENCES
    ))
    # ZI_CUSTOMER --READS_FROM--> T005
    store.add_edge(GraphEdge(
        edge_id="cds_to_tab",
        source_id=cds_id,
        target_id=tab_id,
        relationship=RelationshipType.READS_FROM
    ))
    # CustomerSet --SERVES--> ZI_CUSTOMER
    store.add_edge(GraphEdge(
        edge_id="odata_to_cds",
        source_id=odata_id,
        target_id=cds_id,
        relationship=RelationshipType.SERVES
    ))

    # 2. Build cross link registry
    # Configure path registry mapping to mock hrefs
    path_reg = {
        ("DATA_ELEMENT", "DE_CHAR100"): "ddic/data_elements/de_char100.md",
        ("DOMAIN", "DOM_CHAR100"): "ddic/domains/dom_char100.md",
        ("TABLE", "T005"): "ddic/tables/t005.md",
        ("CDS_VIEW", "ZI_CUSTOMER"): "cds/views/zi_customer.md",
        ("ODATA_ENTITY_SET", "CUSTOMERSET"): "odata/entity_sets/customer_set.md",
    }
    
    registry = build_cross_link_registry(
        path_registry=path_reg,
        graph_store=store,
        artifacts=[]
    )

    # 3. Test walk_chain from DE_CHAR100
    chain = registry.walk_chain("DE_CHAR100", "DATA_ELEMENT")

    # Assert correct length (5 nodes total)
    assert len(chain) == 5

    # Assert correct order of nodes traversed
    targets = [link.target for link in chain]
    assert targets == ["DE_CHAR100", "DOM_CHAR100", "T005", "ZI_CUSTOMER", "CUSTOMERSET"]

    # Assert hrefs resolved correctly via registry
    assert chain[0].href == "ddic/data_elements/de_char100.md"
    assert chain[1].href == "ddic/domains/dom_char100.md"
    assert chain[2].href == "ddic/tables/t005.md"
    assert chain[3].href == "cds/views/zi_customer.md"
    assert chain[4].href == "odata/entity_sets/customer_set.md"

    # Assert stable IDs mapped correctly
    assert chain[0].stable_id == de_id
    assert chain[1].stable_id == dom_id
    assert chain[2].stable_id == tab_id
    assert chain[3].stable_id == cds_id
    assert chain[4].stable_id == odata_id

    # 4. Assert related_ddic_chain redirects to walk_chain
    chain_alias = registry.related_ddic_chain("DE_CHAR100")
    assert [link.target for link in chain_alias] == ["DE_CHAR100", "DOM_CHAR100", "T005", "ZI_CUSTOMER", "CUSTOMERSET"]


def test_importance_scoring():
    store = ArtifactGraphStore()

    de_id = "DDIC::DE:DE_CHAR100"
    dom_id = "DDIC::DOM:DOM_CHAR100"
    tab_id = "DDIC::T005"

    store.add_node(GraphNode(node_id=de_id, node_kind="dataset", label="DE_CHAR100", namespace="DDIC::"))
    store.add_node(GraphNode(node_id=dom_id, node_kind="dataset", label="DOM_CHAR100", namespace="DDIC::"))
    store.add_node(GraphNode(node_id=tab_id, node_kind="dataset", label="T005", namespace="DDIC::"))

    # DE_CHAR100 --REFERENCES--> DOM_CHAR100
    store.add_edge(GraphEdge(edge_id="e1", source_id=de_id, target_id=dom_id, relationship=RelationshipType.REFERENCES))
    # DOM_CHAR100 --REFERENCES--> T005
    store.add_edge(GraphEdge(edge_id="e2", source_id=dom_id, target_id=tab_id, relationship=RelationshipType.REFERENCES))

    path_reg = {
        ("DATA_ELEMENT", "DE_CHAR100"): "ddic/data_elements/de_char100.md",
        ("DOMAIN", "DOM_CHAR100"): "ddic/domains/dom_char100.md",
        ("TABLE", "T005"): "ddic/tables/t005.md",
    }

    registry = build_cross_link_registry(
        path_registry=path_reg,
        graph_store=store,
        artifacts=[]
    )

    # Test resolve_link sets importance score
    link_de = registry.resolve_link("DATA_ELEMENT", "DE_CHAR100")
    assert link_de.importance_score == 1.0

    link_dom = registry.resolve_link("DOMAIN", "DOM_CHAR100")
    assert link_dom.importance_score == 2.0

    link_tab = registry.resolve_link("TABLE", "T005")
    assert link_tab.importance_score == 1.0

    # Add highly central node: "MOST_IMPORTANT"
    store.add_node(GraphNode(node_id="DDIC::MOST_IMPORTANT", node_kind="dataset", label="MOST_IMPORTANT", namespace="DDIC::"))
    store.add_edge(GraphEdge(edge_id="e3", source_id=de_id, target_id="DDIC::MOST_IMPORTANT", relationship=RelationshipType.REFERENCES))
    store.add_edge(GraphEdge(edge_id="e4", source_id=dom_id, target_id="DDIC::MOST_IMPORTANT", relationship=RelationshipType.REFERENCES))
    store.add_edge(GraphEdge(edge_id="e5", source_id=tab_id, target_id="DDIC::MOST_IMPORTANT", relationship=RelationshipType.REFERENCES))
    store.add_edge(GraphEdge(edge_id="e6", source_id="DDIC::OTHER", target_id="DDIC::MOST_IMPORTANT", relationship=RelationshipType.REFERENCES))

    registry._degrees = {}

    neighbors = registry.neighbors_for_render(de_id, [RelationshipType.REFERENCES])
    # The first node returned should be MOST_IMPORTANT because it has the highest degree centrality (5.0)
    assert neighbors[0][0].label == "MOST_IMPORTANT"

