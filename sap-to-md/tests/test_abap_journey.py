from __future__ import annotations

import tempfile
from pathlib import Path
from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.abap_journey.loaders import SourceLoader, StatementCache
from md_generator.sap.abap_journey.resolver import (
    AbapBlockParser,
    SymbolRepository,
)
from md_generator.sap.abap_journey.models import CallGraph, Node, Edge, RelationshipType
from md_generator.sap.abap_journey.graph_builder import CallGraphBuilder
from md_generator.sap.abap_journey.journey_builder import JourneyBuilder
from md_generator.sap.abap_journey.cache import IncrementalCache
from md_generator.sap.abap_journey.renderers.markdown import MarkdownRenderer
from md_generator.sap.abap_journey.renderers.mermaid import MermaidRenderer
from md_generator.sap.abap_journey.renderers.json_renderer import JsonRenderer
from md_generator.sap.abap_journey.renderers.graphviz import GraphvizRenderer
from md_generator.sap.core.run_config import AbapJourneySection

def test_block_parser_and_resolver():
    statements = [
        (1, "REPORT ZTEST_PROG."),
        (3, "INITIALIZATION."),
        (4, "PERFORM INIT_VARS."),
        (6, "START-OF-SELECTION."),
        (7, "CALL FUNCTION 'Z_FETCH_CUSTOMER'."),
        (8, "PERFORM PROCESS_DATA."),
        (10, "FORM INIT_VARS."),
        (11, "lv_initialized = 'X'."),
        (12, "ENDFORM."),
        (14, "FORM PROCESS_DATA."),
        (15, "CALL METHOD cl_processor=>run."),
        (16, "ENDFORM.")
    ]

    blocks = AbapBlockParser.parse_statements(statements)
    
    assert len(blocks) == 5
    assert blocks[0].name == "LOAD-OF-PROGRAM"

    assert blocks[1].kind == "EVENT"
    assert blocks[1].name == "INITIALIZATION"
    assert len(blocks[1].calls) == 1
    assert blocks[1].calls[0].call_type == "PERFORM"
    assert blocks[1].calls[0].target == "INIT_VARS"
    assert blocks[1].calls[0].line == 4

    assert blocks[2].kind == "EVENT"
    assert blocks[2].name == "START-OF-SELECTION"
    assert len(blocks[2].calls) == 2
    assert blocks[2].calls[0].call_type == "CALL_FUNCTION"
    assert blocks[2].calls[0].target == "Z_FETCH_CUSTOMER"
    assert blocks[2].calls[1].call_type == "PERFORM"
    assert blocks[2].calls[1].target == "PROCESS_DATA"

    assert blocks[3].kind == "FORM"
    assert blocks[3].name == "INIT_VARS"

    assert blocks[4].kind == "FORM"
    assert blocks[4].name == "PROCESS_DATA"
    assert len(blocks[4].calls) == 1
    assert blocks[4].calls[0].call_type == "CALL_METHOD"
    assert blocks[4].calls[0].target == "CL_PROCESSOR=>RUN"

def test_include_resolution_and_inlining():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        parent_file = tmp_path / "zparent.abap"
        parent_file.write_text("REPORT ZPARENT.\nSTART-OF-SELECTION.\nINCLUDE zchild.\n", encoding="utf-8")
        
        child_file = tmp_path / "zchild.abap"
        child_file.write_text("FORM CHILD_FORM.\nlv_val = 1.\nENDFORM.\n", encoding="utf-8")
        
        parent_art = CanonicalArtifact(
            identity={"stable_id": "ABAP::ZPARENT", "display_id": "ZPARENT"},
            provenance={"source_files": [str(parent_file)]},
            artifact_type="abap.program",
            name="ZPARENT",
            source_path=str(parent_file)
        )
        child_art = CanonicalArtifact(
            identity={"stable_id": "ABAP::ZCHILD", "display_id": "ZCHILD"},
            provenance={"source_files": [str(child_file)]},
            artifact_type="abap.program",
            name="ZCHILD",
            source_path=str(child_file)
        )
        
        loader = SourceLoader({"ZPARENT": parent_art, "ZCHILD": child_art})
        cache = StatementCache()
        repo = SymbolRepository(loader, cache)
        
        res = loader.load_source("ZPARENT", parent_file)
        assert res is not None
        source_content, path = res
        stmts = cache.get_statements(path, source_content)
        assert len(stmts) == 3
        
        inlined = CallGraphBuilder.inline_includes(stmts, repo, {"ZPARENT"}, parent_file)
        assert any("FORM CHILD_FORM" in s[1] for s in inlined)

def test_cycle_recursion_protection():
    code_content = """REPORT ZRECURSIVE.
START-OF-SELECTION.
PERFORM FORM_A.
FORM FORM_A.
PERFORM FORM_B.
ENDFORM.
FORM FORM_B.
PERFORM FORM_A.
ENDFORM.
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        prog_file = tmp_path / "zrecursive.abap"
        prog_file.write_text(code_content, encoding="utf-8")
        
        art = CanonicalArtifact(
            identity={"stable_id": "ABAP::ZRECURSIVE", "display_id": "ZRECURSIVE"},
            provenance={"source_files": [str(prog_file)]},
            artifact_type="abap.program",
            name="ZRECURSIVE",
            source_path=str(prog_file)
        )
        
        loader = SourceLoader({"ZRECURSIVE": art})
        cache = StatementCache()
        repo = SymbolRepository(loader, cache)
        
        config = AbapJourneySection(max_depth=50, stop_at_sap_standard=False)
        graph = CallGraphBuilder.build_graph_for_program("ZRECURSIVE", repo, config, prog_file)
        
        # Verify cycles resolved and marked correctly on nodes
        node_a_id = "form://ZRECURSIVE/FORM_A"
        node_b_id = "form://ZRECURSIVE/FORM_B"
        
        assert node_a_id in graph.nodes
        assert node_b_id in graph.nodes
        assert graph.nodes[node_a_id].has_cycle is True

def test_sap_standard_stopping():
    code_content = """REPORT ZSAP_STOP.
START-OF-SELECTION.
CALL FUNCTION 'BAPI_CUSTOMER_GETDETAIL'.
CALL FUNCTION 'Z_MY_CUSTOM_FUNC'.
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        prog_file = tmp_path / "zsap_stop.abap"
        prog_file.write_text(code_content, encoding="utf-8")

        art = CanonicalArtifact(
            identity={"stable_id": "ABAP::ZSAP_STOP", "display_id": "ZSAP_STOP"},
            provenance={"source_files": [str(prog_file)]},
            artifact_type="abap.program",
            name="ZSAP_STOP",
            source_path=str(prog_file)
        )

        loader = SourceLoader({"ZSAP_STOP": art})
        cache = StatementCache()
        repo = SymbolRepository(loader, cache)

        config = AbapJourneySection(stop_at_sap_standard=True, customer_namespaces=["Z*"])
        graph = CallGraphBuilder.build_graph_for_program("ZSAP_STOP", repo, config, prog_file)

        bapi_node_id = "standard://BAPI_CUSTOMER_GETDETAIL"
        custom_node_id = "func://Z_MY_CUSTOM_FUNC"

        assert bapi_node_id in graph.nodes
        assert graph.nodes[bapi_node_id].is_sap is True
        assert graph.nodes[bapi_node_id].kind == "STANDARD_SAP"

        assert custom_node_id in graph.nodes
        assert graph.nodes[custom_node_id].is_sap is False

def test_end_to_end_journey_markdown():
    graph = CallGraph()
    prog_id = "prog://ZMY_PROG"
    event_id = "event://ZMY_PROG/START-OF-SELECTION"
    form_id = "form://ZMY_PROG/PROCESS_LOGIC"
    func_id = "func://BAPI_USER_GET_DETAIL"

    graph.add_node(Node(id=prog_id, kind="PROGRAM", name="ZMY_PROG", program="ZMY_PROG"))
    graph.add_node(Node(id=event_id, kind="EVENT", name="START-OF-SELECTION", program="ZMY_PROG"))
    graph.add_node(Node(id=form_id, kind="FORM", name="PROCESS_LOGIC", program="ZMY_PROG", line=12))
    graph.add_node(Node(id=func_id, kind="CALL_FUNCTION", name="BAPI_USER_GET_DETAIL", program="ZMY_PROG", line=15, is_sap=True))

    graph.add_edge(Edge(source=prog_id, destination=event_id, relationship=RelationshipType.INCLUDES))
    graph.add_edge(Edge(source=event_id, destination=form_id, relationship=RelationshipType.PERFORMS, line_number=12))
    graph.add_edge(Edge(source=form_id, destination=func_id, relationship=RelationshipType.CALLS, line_number=15))

    phases = JourneyBuilder.build_phases(graph)
    markdown = MarkdownRenderer.render("ZMY_PROG", graph, phases)

    # Assert headers and structure
    assert "## ABAP Execution Journey" in markdown
    assert "Phase: START-OF-SELECTION" in markdown
    assert "└── FORM: PROCESS_LOGIC @ line 12" in markdown
    assert "    └── CALL_FUNCTION: BAPI_USER_GET_DETAIL (SAP Standard) @ line 15" in markdown
    assert "## Call Graph Visualization" in markdown
    assert "```mermaid" in markdown
    assert "## Static Analysis Statistics" in markdown

def test_incremental_cache():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        cache_dir = tmp_path / "cache"
        prog_file = tmp_path / "zcached.abap"
        prog_file.write_text("REPORT ZCACHED.\n", encoding="utf-8")

        graph = CallGraph()
        prog_id = "prog://ZCACHED"
        graph.add_node(Node(id=prog_id, kind="PROGRAM", name="ZCACHED", program="ZCACHED"))

        cache = IncrementalCache(cache_dir)
        cache.put(prog_file, graph)

        cached_graph = cache.get(prog_file)
        assert cached_graph is not None
        assert prog_id in cached_graph.nodes
        assert cached_graph.nodes[prog_id].name == "ZCACHED"

def test_renderers():
    graph = CallGraph()
    prog_id = "prog://ZMY_PROG"
    event_id = "event://ZMY_PROG/START-OF-SELECTION"

    graph.add_node(Node(id=prog_id, kind="PROGRAM", name="ZMY_PROG"))
    graph.add_node(Node(id=event_id, kind="EVENT", name="START-OF-SELECTION"))
    graph.add_edge(Edge(source=prog_id, destination=event_id, relationship=RelationshipType.INCLUDES))

    mermaid_out = MermaidRenderer.render(graph)
    assert "graph TD" in mermaid_out
    assert f"-->|{RelationshipType.INCLUDES.value}|" in mermaid_out

    json_out = JsonRenderer.render(graph)
    assert '"nodes":' in json_out

    graphviz_out = GraphvizRenderer.render(graph)
    assert "digraph G {" in graphviz_out
