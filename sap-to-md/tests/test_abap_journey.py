from __future__ import annotations

import tempfile
from pathlib import Path
from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.abap_journey.loaders import SourceLoader, StatementCache
from md_generator.sap.abap_journey.resolver import (
    AbapBlockParser,
    SymbolRepository,
)
from md_generator.sap.abap_journey.models import (
    CallGraph,
    Node,
    Edge,
    RelationshipType,
    ResolutionStatus,
    GraphSerializer,
)
from md_generator.sap.abap_journey.graph_builder import CallGraphBuilder
from md_generator.sap.abap_journey.journey_builder import JourneyBuilder
from md_generator.sap.abap_journey.cache import IncrementalCache
from md_generator.sap.abap_journey.renderers.markdown import MarkdownRenderer
from md_generator.sap.abap_journey.renderers.mermaid import MermaidRenderer
from md_generator.sap.abap_journey.renderers.json_renderer import JsonRenderer
from md_generator.sap.abap_journey.renderers.graphviz import GraphvizRenderer
from md_generator.sap.core.run_config import AbapJourneySection, TraversalConfig

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
        
        config = AbapJourneySection(traversal=TraversalConfig(max_depth=50, stop_at_sap_standard=False))
        graph = CallGraphBuilder.build_graph_for_program("ZRECURSIVE", repo, config, prog_file)
        
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
CALL FUNCTION '/DEPT/MY_FUNC'.
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

        # Configure custom namespaces list dynamically
        config = AbapJourneySection(traversal=TraversalConfig(
            stop_at_sap_standard=True,
            customer_namespaces=["Z*", "/DEPT/*"]
        ))
        graph = CallGraphBuilder.build_graph_for_program("ZSAP_STOP", repo, config, prog_file)

        bapi_node_id = "standard://BAPI_CUSTOMER_GETDETAIL"
        custom_node_id = "func://Z_MY_CUSTOM_FUNC"
        dept_node_id = "func:///DEPT/MY_FUNC"

        assert bapi_node_id in graph.nodes
        assert graph.nodes[bapi_node_id].is_standard is True
        assert graph.nodes[bapi_node_id].kind == "STANDARD_SAP"

        assert custom_node_id in graph.nodes
        assert graph.nodes[custom_node_id].is_standard is False

        assert dept_node_id in graph.nodes
        assert graph.nodes[dept_node_id].is_standard is False

def test_end_to_end_journey_markdown():
    graph = CallGraph()
    prog_id = "prog://ZMY_PROG"
    event_id = "event://ZMY_PROG/START-OF-SELECTION"
    form_id = "form://ZMY_PROG/PROCESS_LOGIC"
    func_id = "func://BAPI_USER_GET_DETAIL"

    graph.add_node(Node(id=prog_id, kind="PROGRAM", name="ZMY_PROG", program="ZMY_PROG"))
    graph.add_node(Node(id=event_id, kind="EVENT", name="START-OF-SELECTION", program="ZMY_PROG"))
    graph.add_node(Node(id=form_id, kind="FORM", name="PROCESS_LOGIC", program="ZMY_PROG", line=12))
    graph.add_node(Node(id=func_id, kind="CALL_FUNCTION", name="BAPI_USER_GET_DETAIL", program="ZMY_PROG", line=15, is_standard=True))

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

def test_graph_query_apis():
    graph = CallGraph()
    prog = Node(id="prog://ZTEST", kind="PROGRAM", name="ZTEST")
    event = Node(id="event://ZTEST/START", kind="EVENT", name="START")
    form = Node(id="form://ZTEST/MY_FORM", kind="FORM", name="MY_FORM")

    graph.add_node(prog)
    graph.add_node(event)
    graph.add_node(form)

    edge1 = Edge(source="prog://ZTEST", destination="event://ZTEST/START", relationship=RelationshipType.INCLUDES)
    edge2 = Edge(source="event://ZTEST/START", destination="form://ZTEST/MY_FORM", relationship=RelationshipType.PERFORMS)
    graph.add_edge(edge1)
    graph.add_edge(edge2)

    assert graph.find_node("prog://ZTEST") == prog
    assert len(graph.successors("prog://ZTEST")) == 1
    assert graph.successors("prog://ZTEST")[0] == event
    assert graph.predecessors("form://ZTEST/MY_FORM")[0] == event
    assert len(graph.roots()) == 1
    assert graph.roots()[0] == prog
    assert len(graph.leaf_nodes()) == 1
    assert graph.leaf_nodes()[0] == form

def test_graph_serializer():
    graph = CallGraph()
    node = Node(id="prog://ZTEST", kind="PROGRAM", name="ZTEST", line_start=1, line_end=10, is_standard=True)
    graph.add_node(node)
    
    edge = Edge(
        source="prog://ZTEST",
        destination="form://ZTEST/XYZ",
        relationship=RelationshipType.PERFORMS,
        resolution_status=ResolutionStatus.DYNAMIC,
        dynamic=True,
        confidence=0.5
    )
    graph.add_edge(edge)

    serialized = GraphSerializer.to_json(graph)
    assert "resolution_status" in serialized
    assert "is_standard" in serialized

    deserialized = GraphSerializer.from_json(serialized)
    assert "prog://ZTEST" in deserialized.nodes
    assert deserialized.nodes["prog://ZTEST"].line_start == 1
    assert len(deserialized.edges) == 1
    assert deserialized.edges[0].resolution_status == ResolutionStatus.DYNAMIC

def test_abap_execution_transitions_and_data_lineage():
    code_content = """REPORT ZTRANSITIONS.
START-OF-SELECTION.
CALL BADI lo_badi->run.
AUTHORITY-CHECK OBJECT 'S_TCODE' ID 'TCD' FIELD 'SE38'.
MESSAGE e001(zmsg).
SUBMIT zjob VIA JOB 'MY_JOB' NUMBER '123'.
SELECT * FROM kna1 INTO TABLE lt_kna1.
UPDATE mara SET vp = 1.
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        prog_file = tmp_path / "ztransitions.abap"
        prog_file.write_text(code_content, encoding="utf-8")

        art = CanonicalArtifact(
            identity={"stable_id": "ABAP::ZTRANSITIONS", "display_id": "ZTRANSITIONS"},
            provenance={"source_files": [str(prog_file)]},
            artifact_type="abap.program",
            name="ZTRANSITIONS",
            source_path=str(prog_file)
        )

        loader = SourceLoader({"ZTRANSITIONS": art})
        cache = StatementCache()
        repo = SymbolRepository(loader, cache)

        config = AbapJourneySection(traversal=TraversalConfig(
            stop_at_sap_standard=False,
            customer_namespaces=["Z*"]
        ))
        graph = CallGraphBuilder.build_graph_for_program("ZTRANSITIONS", repo, config, prog_file)

        # Check nodes
        badi_node_id = "badi://LO_BADI->RUN"
        auth_node_id = "auth://S_TCODE"
        msg_node_id = "message://ZMSG/001"
        job_node_id = "prog://ZJOB"
        kna1_node_id = "table://KNA1"
        mara_node_id = "table://MARA"

        assert badi_node_id in graph.nodes
        assert auth_node_id in graph.nodes
        assert msg_node_id in graph.nodes
        assert job_node_id in graph.nodes
        assert kna1_node_id in graph.nodes
        assert mara_node_id in graph.nodes

        # Check relationships
        edges_from_event = [e for e in graph.edges if e.source == "event://ZTRANSITIONS/START-OF-SELECTION"]
        
        # CHECKS relationship
        auth_edge = next(e for e in edges_from_event if e.destination == auth_node_id)
        assert auth_edge.relationship == RelationshipType.CHECKS

        # READS relationship
        kna1_edge = next(e for e in edges_from_event if e.destination == kna1_node_id)
        assert kna1_edge.relationship == RelationshipType.READS

        # WRITES relationship
        mara_edge = next(e for e in edges_from_event if e.destination == mara_node_id)
        assert mara_edge.relationship == RelationshipType.WRITES

        # SUBMITS relationship
        job_edge = next(e for e in edges_from_event if e.destination == job_node_id)
        assert job_edge.relationship == RelationshipType.SUBMITS

def test_abap_advanced_sap_coverage():
    code_content = """REPORT ZADVANCED.
START-OF-SELECTION.
SELECT * FROM (lv_table) INTO TABLE lt_data.
SELECT * FROM zi_customer INTO TABLE lt_cust.
CALL TRANSACTION lv_tcode.
MESSAGE ID lv_msgid TYPE 'E' NUMBER '001'.
MESSAGE e002(zmsg_class).
GET BADI lo_badi FILTERS country = 'US'.
CALL FUNCTION 'ENQUEUE_EZ_LOCK'.
CALL FUNCTION 'Z_MY_FUNC' DESTINATION 'NONE'.
DEFINE BEHAVIOR FOR z_rap_entity.
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        prog_file = tmp_path / "zadvanced.abap"
        prog_file.write_text(code_content, encoding="utf-8")

        art = CanonicalArtifact(
            identity={"stable_id": "ABAP::ZADVANCED", "display_id": "ZADVANCED"},
            provenance={"source_files": [str(prog_file)]},
            artifact_type="abap.program",
            name="ZADVANCED",
            source_path=str(prog_file)
        )

        loader = SourceLoader({"ZADVANCED": art})
        cache = StatementCache()
        repo = SymbolRepository(loader, cache)

        config = AbapJourneySection(traversal=TraversalConfig(
            stop_at_sap_standard=False,
            customer_namespaces=["Z*"]
        ))
        graph = CallGraphBuilder.build_graph_for_program("ZADVANCED", repo, config, prog_file)

        # 1. Dynamic SELECT table in parenthesis
        dyn_table_node = "table://(LV_TABLE)"
        assert dyn_table_node in graph.nodes
        edges_to_dyn = [e for e in graph.edges if e.destination == dyn_table_node]
        assert len(edges_to_dyn) == 1
        assert edges_to_dyn[0].dynamic is True
        assert edges_to_dyn[0].resolution_status == ResolutionStatus.DYNAMIC

        # 2. CDS View ZI_CUSTOMER
        cds_node = "cds://ZI_CUSTOMER"
        assert cds_node in graph.nodes
        assert graph.nodes[cds_node].kind == "CDS"

        # 3. Dynamic transaction
        dyn_tcode_node = "tcode://LV_TCODE"
        assert dyn_tcode_node in graph.nodes
        edges_to_tcode = [e for e in graph.edges if e.destination == dyn_tcode_node]
        assert edges_to_tcode[0].dynamic is True

        # 4. Dynamic message
        dyn_msg_node = "message://DYNAMIC_MESSAGE"
        assert dyn_msg_node in graph.nodes
        edges_to_msg = [e for e in graph.edges if e.destination == dyn_msg_node]
        assert edges_to_msg[0].dynamic is True

        # 5. Message Class mapping
        msg_node = "message://ZMSG_CLASS/002"
        assert msg_node in graph.nodes

        # 6. Lock Object
        lock_node = "lock://EZ_LOCK"
        assert lock_node in graph.nodes
        assert graph.nodes[lock_node].kind == "LOCK_OBJECT"

        # 7. RFC Destination 'NONE'
        rfc_node = "rfc://Z_MY_FUNC"
        assert rfc_node in graph.nodes
        assert graph.nodes[rfc_node].kind == "RFC"
        assert graph.nodes[rfc_node].metadata.get("destination") == "NONE"

        # 8. RAP Behavior
        rap_node = "behavior://Z_RAP_ENTITY"
        assert rap_node in graph.nodes

def test_abap_journey_fallback_phases():
    graph = CallGraph()
    prog_id = "prog://ZMY_CLASS"
    meth1_id = "method://ZMY_CLASS/RUN"
    meth2_id = "method://ZMY_CLASS/HELP"
    
    graph.add_node(Node(id=prog_id, kind="PROGRAM", name="ZMY_CLASS"))
    graph.add_node(Node(id=meth1_id, kind="METHOD", name="RUN"))
    graph.add_node(Node(id=meth2_id, kind="METHOD", name="HELP"))
    
    graph.add_edge(Edge(source=prog_id, destination=meth1_id, relationship=RelationshipType.CALLS))
    graph.add_edge(Edge(source=prog_id, destination=meth2_id, relationship=RelationshipType.CALLS))
    
    phases = JourneyBuilder.build_phases(graph)
    assert len(phases) == 1
    assert phases[0].phase_name == "Entry Points (Methods / Subroutines / Functions)"
    assert len(phases[0].root_nodes) == 2
    assert any(n.name == "RUN" for n in phases[0].root_nodes)
    assert any(n.name == "HELP" for n in phases[0].root_nodes)

def test_abap_advanced_static_analysis_mappings():
    code_content = """REPORT ZEXTENDED.
START-OF-SELECTION.
INTERFACE zif_test_interface.
INTERFACES zif_test_interface.
AUTHORITY-CHECK OBJECT 'S_TCODE' ID 'TCD' FIELD 'SE38' ID 'ACTVT' FIELD '03'.
MESSAGE e001(zmsg_class).
SUBMIT zjob VIA JOB 'MY_JOB' USING SELECTION-SET 'VAR_A'.
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        prog_file = tmp_path / "zextended.abap"
        prog_file.write_text(code_content, encoding="utf-8")

        art = CanonicalArtifact(
            identity={"stable_id": "ABAP::ZEXTENDED", "display_id": "ZEXTENDED"},
            provenance={"source_files": [str(prog_file)]},
            artifact_type="abap.program",
            name="ZEXTENDED",
            source_path=str(prog_file)
        )

        loader = SourceLoader({"ZEXTENDED": art})
        cache = StatementCache()
        repo = SymbolRepository(loader, cache)

        config = AbapJourneySection(traversal=TraversalConfig(
            stop_at_sap_standard=False,
            customer_namespaces=["Z*"]
        ))
        graph = CallGraphBuilder.build_graph_for_program("ZEXTENDED", repo, config, prog_file)

        # 1. Interface node & edge
        interface_node = "interface://ZIF_TEST_INTERFACE"
        assert interface_node in graph.nodes
        assert graph.nodes[interface_node].kind == "INTERFACE"

        # 2. Authority object with multiple fields/values
        auth_node = "auth://S_TCODE"
        assert auth_node in graph.nodes
        assert graph.nodes[auth_node].metadata.get("tcd") == "SE38"
        assert graph.nodes[auth_node].metadata.get("actvt") == "03"

        # 3. Message class mapping and severity
        msg_node = "message://ZMSG_CLASS/001"
        assert msg_node in graph.nodes
        assert graph.nodes[msg_node].metadata.get("severity") == "E"

        # 4. Job variant matching
        job_node = "prog://ZJOB"
        assert job_node in graph.nodes
        assert graph.nodes[job_node].metadata.get("variant") == "VAR_A"




