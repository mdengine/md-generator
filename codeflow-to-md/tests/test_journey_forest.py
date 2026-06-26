from __future__ import annotations

from md_generator.codeflow.journey import JourneyNodeIR, JourneyIR, JourneyStatistics
from md_generator.codeflow.journey.forest import JourneyForest, ForestMetadata, ForestStatistics


def test_journey_forest_structure() -> None:
    root1 = JourneyNodeIR(id="entry1", label="entry1()", node_type="entry")
    root2 = JourneyNodeIR(id="entry2", label="entry2()", node_type="entry")
    
    ir1 = JourneyIR(root=root1, statistics=JourneyStatistics(node_count=3, maximum_depth=2))
    ir2 = JourneyIR(root=root2, statistics=JourneyStatistics(node_count=5, maximum_depth=4))
    
    fm = ForestMetadata(repository="my_repo", tree_count=2, entry_types={"entry": 2})
    fs = ForestStatistics(
        tree_count=2,
        total_nodes=8,
        max_tree_depth=4,
        avg_tree_depth=3.0,
    )
    
    forest = JourneyForest(trees=[ir1, ir2], metadata=fm, statistics=fs)
    
    assert len(forest.trees) == 2
    assert forest.metadata.repository == "my_repo"
    assert forest.metadata.tree_count == 2
    assert forest.metadata.entry_types["entry"] == 2
    assert forest.statistics.total_nodes == 8
    assert forest.statistics.max_tree_depth == 4
    assert forest.statistics.avg_tree_depth == 3.0
    assert forest.cross_tree_edges == []
