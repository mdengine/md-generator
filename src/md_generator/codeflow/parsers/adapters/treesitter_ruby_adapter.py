"""Tree-sitter Ruby → IRMethod (minimal)."""

from __future__ import annotations

from pathlib import Path

from tree_sitter import Parser

from md_generator.codeflow.models.ir import FileParseResult
from md_generator.codeflow.models.ir_cfg import IRMethod, IRStmt
from md_generator.codeflow.parsers.treesitter_common import decode_text, rel_key, sid
from md_generator.codeflow.parsers.treesitter_ruby_parser import ruby_language


def populate_ir_methods_ruby_treesitter(fr: FileParseResult, project_root: Path) -> None:
    if fr.parse_backend != "treesitter":
        fr.ir_methods = []
        return
    loaded = ruby_language()
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
        stmts: tuple[IRStmt, ...] = tuple(
            IRStmt(kind="STATEMENT", label=c.type, line=c.start_point[0] + 1)
            for c in node.children
            if c.is_named and c.type not in ("end",)
        )
        out.append(
            IRMethod(
                symbol_id=sid(key, fq, mname),
                name=mname,
                file_path=fp,
                language="ruby",
                body=stmts,
            ),
        )

    def visit_class(node, class_stack: list[str]) -> None:  # noqa: ANN001
        name = node.child_by_field_name("name")
        if not name:
            return
        cname = decode_text(source, name).strip()
        if not cname:
            return
        class_stack.append(cname)
        for ch in node.children:
            if ch.type == "class":
                visit_class(ch, class_stack)
            elif ch.type in ("method", "singleton_method"):
                add_method(ch, "::".join(class_stack))
        class_stack.pop()

    for ch in tree.root_node.children:
        if ch.type == "class":
            visit_class(ch, [])
        elif ch.type in ("method", "singleton_method"):
            add_method(ch, None)
    fr.ir_methods = out
