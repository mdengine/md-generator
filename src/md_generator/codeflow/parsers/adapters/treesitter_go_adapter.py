"""Tree-sitter Go → IRMethod (minimal)."""

from __future__ import annotations

from pathlib import Path

from tree_sitter import Parser

from md_generator.codeflow.models.ir import FileParseResult
from md_generator.codeflow.models.ir_cfg import IRMethod, IRStmt
from md_generator.codeflow.parsers.treesitter_common import decode_text, rel_key, sid
from md_generator.codeflow.parsers.treesitter_go_parser import go_language


def populate_ir_methods_go_treesitter(fr: FileParseResult, project_root: Path) -> None:
    if fr.parse_backend != "treesitter":
        fr.ir_methods = []
        return
    loaded = go_language()
    if loaded is None:
        fr.ir_methods = []
        return
    lang, _ = loaded
    source = fr.path.read_bytes()
    tree = Parser(lang).parse(source)
    key = rel_key(fr.path, project_root.resolve())
    fp = str(fr.path.resolve())
    out: list[IRMethod] = []
    for ch in tree.root_node.children:
        if ch.type not in ("function_declaration", "method_declaration"):
            continue
        name = ch.child_by_field_name("name")
        if not name:
            continue
        mname = decode_text(source, name).strip()
        recv = None
        if ch.type == "method_declaration":
            recv_n = ch.child_by_field_name("receiver")
            if recv_n:
                recv = decode_text(source, recv_n).strip().strip("()")
        body = ch.child_by_field_name("body")
        stmts: tuple[IRStmt, ...] = ()
        if body:
            stmts = tuple(
                IRStmt(kind="STATEMENT", label=c.type, line=c.start_point[0] + 1)
                for c in body.children
                if c.is_named
            )
        out.append(
            IRMethod(
                symbol_id=sid(key, recv, mname) if recv else sid(key, None, mname),
                name=mname,
                file_path=fp,
                language="go",
                body=stmts,
            ),
        )
    fr.ir_methods = out
