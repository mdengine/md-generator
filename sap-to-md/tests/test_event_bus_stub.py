from md_generator.sap.framework.events import ArtifactParsedEvent, EventBus, GraphMergedEvent


def test_event_bus_stub():
    bus = EventBus()
    bus.publish(ArtifactParsedEvent(artifact_id="a1", artifact_type="bw.dtp", parser_id="bw.dtp"))
    bus.publish(GraphMergedEvent(graph_id="run", fragment_id="f1", node_count=1, edge_count=0))
    assert len(bus.events) == 2
