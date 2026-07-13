from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.abap_journey.loaders import SourceLoader, StatementCache
from md_generator.sap.abap_journey.extractors import extract_all_calls

from md_generator.sap.abap_journey.models import CallReference, AbapBlock

class ProgramContext:
    def __init__(self, program_name: str, blocks: list[AbapBlock]) -> None:
        self.program_name = program_name.upper()
        self.blocks = blocks
        self.events = [b for b in blocks if b.kind == "EVENT"]
        self.forms = {b.name.upper(): b for b in blocks if b.kind == "FORM"}
        self.methods = {b.name.upper(): b for b in blocks if b.kind == "METHOD"}
        self.functions = {b.name.upper(): b for b in blocks if b.kind == "FUNCTION"}

class AbapBlockParser:
    EVENT_KEYWORDS = {
        "INITIALIZATION",
        "LOAD-OF-PROGRAM",
        "START-OF-SELECTION",
        "END-OF-SELECTION",
        "TOP-OF-PAGE",
        "END-OF-PAGE"
    }

    @staticmethod
    def parse_statements(statements: list[tuple[int, str]]) -> list[AbapBlock]:
        blocks: list[AbapBlock] = []
        current_block: AbapBlock | None = None

        def start_new_block(kind: str, name: str):
            nonlocal current_block
            if current_block and current_block.statements:
                blocks.append(current_block)
            current_block = AbapBlock(kind=kind, name=name)

        # We start with a default block in case statements exist before any event/routine definitions
        current_block = AbapBlock(kind="EVENT", name="LOAD-OF-PROGRAM")
        in_definition = False
        def_kind = ""
        def_name = ""

        for line_no, stmt in statements:
            upper = stmt.strip().upper()
            if not upper:
                continue

            form_match = re.match(r"^FORM\s+([\w/]+)", upper)
            method_match = re.match(r"^METHOD\s+([\w/=>\-]+)", upper)
            func_match = re.match(r"^FUNCTION\s+([\w/]+)", upper)

            is_end = False
            if upper.startswith("ENDFORM"):
                is_end = True
            elif upper.startswith("ENDMETHOD"):
                is_end = True
            elif upper.startswith("ENDFUNCTION"):
                is_end = True

            if form_match or method_match or func_match:
                in_definition = True
                if form_match:
                    def_kind, def_name = "FORM", form_match.group(1)
                elif method_match:
                    def_kind, def_name = "METHOD", method_match.group(1)
                else:
                    def_kind, def_name = "FUNCTION", func_match.group(1)

                start_new_block(def_kind, def_name)
                current_block.statements.append((line_no, stmt))
                continue
            elif is_end:
                if current_block:
                    current_block.statements.append((line_no, stmt))
                    blocks.append(current_block)
                current_block = AbapBlock(kind="EVENT", name="START-OF-SELECTION")
                in_definition = False
                continue

            if not in_definition:
                is_event = False
                event_name = ""
                for kw in AbapBlockParser.EVENT_KEYWORDS:
                    if upper.startswith(kw):
                        is_event = True
                        event_name = kw
                        break
                if upper.startswith("AT SELECTION-SCREEN"):
                    is_event = True
                    event_name = stmt.strip()

                if is_event:
                    start_new_block("EVENT", event_name)
                    current_block.statements.append((line_no, stmt))
                    continue

            if current_block:
                current_block.statements.append((line_no, stmt))

        if current_block and current_block.statements:
            blocks.append(current_block)

        # Parse calls inside blocks using CallExtractor plugins
        for block in blocks:
            block.calls = AbapBlockParser.extract_calls(block.statements)

        return blocks

    @staticmethod
    def extract_calls(statements: list[tuple[int, str]]) -> list[CallReference]:
        calls: list[CallReference] = []
        for line_no, stmt in statements:
            calls.extend(extract_all_calls(stmt, line_no))
        return calls

class SymbolRepository:
    def __init__(self, loader: SourceLoader, cache: StatementCache) -> None:
        self.loader = loader
        self.cache = cache
        
        # Pre-built indices (populated dynamically on demand)
        self.program_contexts: dict[str, ProgramContext] = {}
        self.form_index: dict[tuple[str, str], AbapBlock] = {}      # (program, form) -> block
        self.method_index: dict[tuple[str, str], AbapBlock] = {}    # (class, method) -> block
        self.function_index: dict[str, AbapBlock] = {}              # function -> block
        self.program_index: dict[str, Path] = {}                    # program -> source path

    def index_program(self, program_name: str, parent_path: Path | None = None) -> ProgramContext | None:
        prog_upper = program_name.upper()
        if prog_upper in self.program_contexts:
            return self.program_contexts[prog_upper]

        res = self.loader.load_source(prog_upper, parent_path)
        if not res:
            return None
        
        source_content, path = res
        self.program_index[prog_upper] = path
        
        stmts = self.cache.get_statements(path, source_content)
        blocks = AbapBlockParser.parse_statements(stmts)
        ctx = ProgramContext(prog_upper, blocks)
        
        # Populate indices
        self.program_contexts[prog_upper] = ctx
        
        for name, block in ctx.forms.items():
            self.form_index[(prog_upper, name)] = block
        for name, block in ctx.methods.items():
            self.method_index[(prog_upper, name)] = block
        for name, block in ctx.functions.items():
            self.function_index[name] = block
            
        return ctx

    def find_form(self, program: str, form: str, parent_path: Path | None = None) -> AbapBlock | None:
        prog_upper = program.upper()
        form_upper = form.upper()
        
        # Ensure program is indexed
        self.index_program(prog_upper, parent_path)
        return self.form_index.get((prog_upper, form_upper))

    def find_method(self, class_name: str, method_name: str, parent_path: Path | None = None) -> AbapBlock | None:
        cls_upper = class_name.upper()
        meth_upper = method_name.upper()
        
        self.index_program(cls_upper, parent_path)
        return self.method_index.get((cls_upper, meth_upper))

    def find_program(self, name: str, parent_path: Path | None = None) -> Path | None:
        prog_upper = name.upper()
        self.index_program(prog_upper, parent_path)
        return self.program_index.get(prog_upper)

    def find_function(self, name: str, parent_path: Path | None = None) -> AbapBlock | None:
        func_upper = name.upper()
        
        # Functions are defined in function groups (usually SAPL<group>).
        # We can scan the loader's artifacts directly for the function metadata,
        # or load the function group if we know it.
        # As an easy lookup, we also check if the function was already indexed.
        if func_upper in self.function_index:
            return self.function_index[func_upper]
            
        # Fallback: scan all function module objects in loaders to index their group
        for art_name, art in self.loader.artifacts.items():
            if art.artifact_type == "abap.program" and func_upper in art_name:
                self.index_program(art_name, parent_path)
                if func_upper in self.function_index:
                    return self.function_index[func_upper]
        return None
