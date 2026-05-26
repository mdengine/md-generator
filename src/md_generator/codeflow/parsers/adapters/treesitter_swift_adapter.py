"""Tree-sitter Swift → IRMethod (minimal)."""

from __future__ import annotations

from pathlib import Path

from tree_sitter import Parser

from md_generator.codeflow.models.ir import FileParseResult
from md_generator.codeflow.models.ir_cfg import IRMethod, IRStmt
from md_generator.codeflow.parsers.treesitter_common import decode_text, function_body_node, rel_key, sid
from md_generator.codeflow.parsers.treesitter_swift_parser import swift_language


def populate_ir_methods_swift_treesitter(fr: FileParseResult, project_root: Path) -> None:
    if fr.parse_backend != "treesitter":
        fr.ir_methods = []
        return
    loaded = swift_language()
    if loaded is None:
        fr.ir_methods = []
        return
    lang, _ = loaded
    source = fr.path.read_bytes()
    tree = Parser(lang).parse(source)
    key = rel_key(fr.path, project_root.resolve())
    fp = str(fr.path.resolve())
    out: list[IRMethod] = []

    def add_method(node, fq: str | None) -> None:  # noqa: ANN001
        name = node.child_by_field_name("name")
        if not name:
            return
        mname = decode_text(source, name).strip()
        body = function_body_node(node)
        stmts: tuple[IRStmt, ...] = ()
        if body:
            stmts = tuple(
                IRStmt(kind="STATEMENT", label=c.type, line=c.start_point[0] + 1)
                for c in body.children
                if c.is_named
            )
        out.append(
            IRMethod(
                symbol_id=sid(key, fq, mname),
                name=mname,
                file_path=fp,
                language="swift",
                body=stmts,
            ),
        )

    def visit_type(node, type_stack: list[str]) -> None:  # noqa: ANN001
        name = node.child_by_field_name("name")
        if not name:
            return
        type_stack.append(decode_text(source, name).strip())
        for ch in node.children:
            if ch.type == "function_declaration":
                add_method(ch, ".".join(type_stack))
            elif ch.type in ("class_declaration", "struct_declaration"):
                visit_type(ch, type_stack)
        type_stack.pop()

    for ch in tree.root_node.children:
        if ch.type in ("class_declaration", "struct_declaration"):
            visit_type(ch, [])
        elif ch.type == "function_declaration":
            add_method(ch, None)
    fr.ir_methods = out
