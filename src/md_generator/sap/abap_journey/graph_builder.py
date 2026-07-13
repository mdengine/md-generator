from __future__ import annotations

import re
import fnmatch
from pathlib import Path
from md_generator.sap.abap_journey.resolver import (
    AbapBlock,
    AbapBlockParser,
    CallReference,
    SymbolRepository,
    ProgramContext,
)
from md_generator.sap.abap_journey.models import CallGraph, Node, Edge, RelationshipType, ResolutionStatus
from md_generator.sap.core.run_config import AbapJourneySection

class CallGraphBuilder:
    @staticmethod
    def is_sap_standard_name(name: str, config: AbapJourneySection) -> bool:
        upper_name = name.upper()
        for pat in config.traversal.customer_namespaces:
            if fnmatch.fnmatch(upper_name, pat.upper()):
                return False
        return True

    @staticmethod
    def get_node_id(kind: str, name: str, program: str = "") -> str:
        k = kind.lower()
        n = name.upper()
        p = program.upper()
        if k in ("event",):
            return f"event://{p}/{n}"
        if k in ("form", "perform", "perform_in_program"):
            return f"form://{p}/{n}"
        if k in ("method", "call_method"):
            if "=>" in n:
                cls, _, meth = n.partition("=>")
                return f"method://{cls.upper()}/{meth.upper()}"
            return f"method://{p}/{n}"
        if k in ("function", "call_function"):
            return f"func://{n}"
        if k in ("program", "submit"):
            return f"prog://{n}"
        if k in ("transaction", "call_transaction"):
            return f"tcode://{n}"
        if k in ("screen", "call_screen"):
            return f"screen://{p}/{n}"
        if k in ("include",):
            return f"incl://{n}"
        if k in ("class", "create_object", "new"):
            return f"class://{n}"
        if k == "standard_sap":
            return f"standard://{n}"
        return f"unknown://{n}"

    @staticmethod
    def inline_includes(
        statements: list[tuple[int, str]],
        repo: SymbolRepository,
        visited_includes: set[str],
        parent_path: Path | None = None
    ) -> list[tuple[int, str]]:
        inlined: list[tuple[int, str]] = []
        for line_no, stmt in statements:
            upper = stmt.strip().upper()
            if upper.startswith("INCLUDE"):
                incl_match = re.match(r"^INCLUDE\s+([\w/]+)", upper)
                if incl_match:
                    incl_name = incl_match.group(1).upper()
                    if incl_name in visited_includes:
                        continue
                    visited_includes.add(incl_name)
                    
                    incl_path = repo.find_program(incl_name, parent_path)
                    incl_stmts = None
                    if incl_path:
                        incl_stmts = repo.cache.get_statements(incl_path)
                        
                    if incl_stmts:
                        resolved_incl = CallGraphBuilder.inline_includes(
                            incl_stmts, repo, visited_includes, incl_path
                        )
                        inlined.extend(resolved_incl)
                    else:
                        inlined.append((line_no, stmt))
                    continue
            inlined.append((line_no, stmt))
        return inlined

    @staticmethod
    def build_graph_for_program(
        program_name: str,
        repo: SymbolRepository,
        config: AbapJourneySection,
        parent_path: Path | None = None
    ) -> CallGraph:
        graph = CallGraph()

        # Resolve statements
        stmts = None
        if parent_path and parent_path.exists():
            stmts = repo.cache.get_statements(parent_path)
        if not stmts:
            res = repo.loader.load_source(program_name, parent_path)
            if not res:
                return graph
            source_content, path = res
            stmts = repo.cache.get_statements(path, source_content)

        inlined = CallGraphBuilder.inline_includes(stmts, repo, {program_name.upper()}, parent_path)
        blocks = AbapBlockParser.parse_statements(inlined)
        prog_ctx = ProgramContext(program_name, blocks)

        # Populate SymbolRepository indexes for the program context
        repo.program_contexts[program_name.upper()] = prog_ctx
        for name, block in prog_ctx.forms.items():
            repo.form_index[(program_name.upper(), name)] = block
        for name, block in prog_ctx.methods.items():
            repo.method_index[(program_name.upper(), name)] = block
        for name, block in prog_ctx.functions.items():
            repo.function_index[name] = block

        # Add program root node
        prog_node_id = f"prog://{program_name.upper()}"
        graph.add_node(Node(
            id=prog_node_id,
            kind="PROGRAM",
            name=program_name.upper(),
            program=program_name.upper(),
            source_file=str(parent_path) if parent_path else ""
        ))

        for event in prog_ctx.events:
            event_id = CallGraphBuilder.get_node_id("event", event.name, program_name)
            graph.add_node(Node(
                id=event_id,
                kind="EVENT",
                name=event.name,
                program=program_name.upper()
            ))
            # Link program to event block
            graph.add_edge(Edge(
                source=prog_node_id,
                destination=event_id,
                relationship=RelationshipType.INCLUDES
            ))

            for call in event.calls:
                CallGraphBuilder.traverse_call(
                    call, event_id, prog_ctx, repo, config, graph, set(), 1, parent_path
                )

        return graph

    @staticmethod
    def traverse_call(
        call: CallReference,
        parent_node_id: str,
        prog_ctx: ProgramContext,
        repo: SymbolRepository,
        config: AbapJourneySection,
        graph: CallGraph,
        path_visited: set[str],
        current_depth: int,
        parent_path: Path | None = None
    ) -> None:
        target_upper = call.target.upper()
        
        # Check standard SAP
        is_sap = False
        if call.call_type in ("CALL_FUNCTION", "CALL_METHOD", "SUBMIT", "CALL_TRANSACTION"):
            is_sap = CallGraphBuilder.is_sap_standard_name(call.target, config)

        call_type_to_kind = {
            "PERFORM": "FORM",
            "PERFORM_IN_PROGRAM": "FORM",
            "CALL_FUNCTION": "FUNCTION",
            "CALL_METHOD": "METHOD",
            "INCLUDE": "INCLUDE",
            "SUBMIT": "PROGRAM",
            "CALL_TRANSACTION": "TRANSACTION",
            "CALL_SCREEN": "SCREEN",
            "CREATE_OBJECT": "CLASS",
            "NEW": "CLASS",
        }
        kind = call_type_to_kind.get(call.call_type, call.call_type)
        if is_sap and config.traversal.stop_at_sap_standard:
            kind = "STANDARD_SAP"

        node_id = CallGraphBuilder.get_node_id(kind, call.target, prog_ctx.program_name)

        namespace = ""
        if "/" in target_upper:
            parts = target_upper.split("/")
            if len(parts) >= 3:
                namespace = f"/{parts[1]}/"
        elif target_upper.startswith("Z"):
            namespace = "Z"
        elif target_upper.startswith("Y"):
            namespace = "Y"
        else:
            namespace = "SAP"

        if node_id not in graph.nodes:
            graph.add_node(Node(
                id=node_id,
                kind=kind,
                name=call.target,
                namespace=namespace,
                program=prog_ctx.program_name,
                line=call.line,
                is_standard=is_sap,
                is_external=(call.call_type == "PERFORM_IN_PROGRAM" or not is_sap and not prog_ctx.forms.get(target_upper))
            ))

        rel = RelationshipType.CALLS
        if call.call_type == "PERFORM" or call.call_type == "PERFORM_IN_PROGRAM":
            rel = RelationshipType.PERFORMS
        elif call.call_type == "INCLUDE":
            rel = RelationshipType.INCLUDES
        elif call.call_type in ("CREATE_OBJECT", "NEW"):
            rel = RelationshipType.CREATES
        elif call.call_type == "SUBMIT":
            rel = RelationshipType.SUBMITS

        # Dynamic call resolution status
        res_status = ResolutionStatus.STATIC
        is_resolved = True
        confidence = 1.0

        if call.dynamic:
            res_status = ResolutionStatus.DYNAMIC
            confidence = 0.5
        else:
            # Check static lookup status in indices
            has_definition = False
            if call.call_type == "PERFORM":
                has_definition = repo.find_form(prog_ctx.program_name, call.target, parent_path) is not None
            elif call.call_type == "PERFORM_IN_PROGRAM":
                has_definition = repo.find_form(call.extra, call.target, parent_path) is not None
            elif call.call_type == "CALL_FUNCTION":
                has_definition = is_sap or repo.find_function(call.target, parent_path) is not None
            elif call.call_type == "CALL_METHOD":
                if "=>" in call.target:
                    cls_name, _, meth_name = call.target.partition("=>")
                    has_definition = repo.find_method(cls_name, meth_name, parent_path) is not None
                else:
                    has_definition = True  # Instance call fallback
            else:
                has_definition = True

            if not has_definition:
                res_status = ResolutionStatus.UNRESOLVED
                is_resolved = False
                confidence = 0.0

        graph.add_edge(Edge(
            source=parent_node_id,
            destination=node_id,
            relationship=rel,
            line_number=call.line,
            resolved=is_resolved,
            dynamic=call.dynamic,
            confidence=confidence,
            resolution_status=res_status
        ))

        if is_sap and config.traversal.stop_at_sap_standard:
            return
        if current_depth > config.traversal.max_depth:
            return

        node_key = f"{call.call_type}:{target_upper}"
        if call.call_type == "PERFORM_IN_PROGRAM":
            node_key = f"{call.call_type}:{call.extra.upper()}:{target_upper}"

        if node_key in path_visited:
            graph.nodes[node_id].has_cycle = True
            return

        path_visited.add(node_key)

        if call.call_type == "PERFORM" and config.traversal.expand_forms:
            form_block = repo.find_form(prog_ctx.program_name, call.target, parent_path)
            if form_block:
                for c in form_block.calls:
                    CallGraphBuilder.traverse_call(
                        c, node_id, prog_ctx, repo, config, graph, path_visited, current_depth + 1, parent_path
                    )

        elif call.call_type == "PERFORM_IN_PROGRAM" and config.traversal.expand_forms:
            ext_prog = call.extra.upper()
            form_block = repo.find_form(ext_prog, call.target, parent_path)
            if form_block:
                ext_ctx = repo.program_contexts.get(ext_prog)
                if ext_ctx:
                    for c in form_block.calls:
                        CallGraphBuilder.traverse_call(
                            c, node_id, ext_ctx, repo, config, graph, path_visited, current_depth + 1, parent_path
                        )

        elif call.call_type == "CALL_FUNCTION" and config.traversal.expand_functions:
            func_block = repo.find_function(call.target, parent_path)
            if func_block:
                func_group = func_block.name.upper()
                func_ctx = repo.program_contexts.get(func_group)
                if not func_ctx:
                    func_ctx = ProgramContext(func_group, [func_block])
                for c in func_block.calls:
                    CallGraphBuilder.traverse_call(
                        c, node_id, func_ctx, repo, config, graph, path_visited, current_depth + 1, parent_path
                    )

        elif call.call_type == "CALL_METHOD" and config.traversal.expand_methods:
            if "=>" in call.target:
                cls_name, _, meth_name = call.target.partition("=>")
                meth_block = repo.find_method(cls_name, meth_name, parent_path)
                if meth_block:
                    cls_ctx = repo.program_contexts.get(cls_name.upper())
                    if not cls_ctx:
                        cls_ctx = ProgramContext(cls_name, [meth_block])
                    for c in meth_block.calls:
                        CallGraphBuilder.traverse_call(
                            c, node_id, cls_ctx, repo, config, graph, path_visited, current_depth + 1, parent_path
                        )

        path_visited.remove(node_key)
