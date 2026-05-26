"""Tree-sitter Rust → IRMethod (minimal)."""

from __future__ import annotations

from pathlib import Path

from tree_sitter import Parser

from md_generator.codeflow.models.ir import FileParseResult
from md_generator.codeflow.models.ir_cfg import IRMethod, IRStmt
from md_generator.codeflow.parsers.treesitter_common import decode_text, rel_key, sid
from md_generator.codeflow.parsers.treesitter_rust_parser import rust_language


def populate_ir_methods_rust_treesitter(fr: FileParseResult, project_root: Path) -> None:
    if fr.parse_backend != "treesitter":
        fr.ir_methods = []
        return
    loaded = rust_language()
    if loaded is None:
        fr.ir_methods = []
        return
    lang, _ = loaded
    source = fr.path.read_bytes()
    tree = Parser(lang).parse(source)
    key = rel_key(fr.path, project_root.resolve())
    fp = str(fr.path.resolve())
    out: list[IRMethod] = []
    impl_type: str | None = None
    stack = [tree.root_node]
    while stack:
        n = stack.pop()
        if n.type == "impl_item":
            ty = n.child_by_field_name("type")
            impl_type = decode_text(source, ty).strip() if ty else None
        elif n.type == "function_item":
            name = n.child_by_field_name("name")
            body = n.child_by_field_name("body")
            if name:
                mname = decode_text(source, name).strip()
                stmts: tuple[IRStmt, ...] = ()
                if body:
                    stmts = tuple(
                        IRStmt(kind="STATEMENT", label=c.type, line=c.start_point[0] + 1)
                        for c in body.children
                        if c.is_named
                    )
                out.append(
                    IRMethod(
                        symbol_id=sid(key, impl_type, mname) if impl_type else sid(key, None, mname),
                        name=mname,
                        file_path=fp,
                        language="rust",
                        body=stmts,
                    ),
                )
        stack.extend(reversed(n.children))
    fr.ir_methods = out
