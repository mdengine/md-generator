"""Tree-sitter Python → IRMethod (minimal CFG IR)."""

from __future__ import annotations

from pathlib import Path

from tree_sitter import Parser

from md_generator.codeflow.models.ir import FileParseResult
from md_generator.codeflow.models.ir_cfg import IRMethod, IRStmt
from md_generator.codeflow.parsers.treesitter_common import decode_text, rel_key, sid, trim
from md_generator.codeflow.parsers.treesitter_python_parser import python_language


def _py_stmt(node, source: bytes) -> IRStmt | None:  # noqa: ANN001
    line = node.start_point[0] + 1
    t = node.type
    if t == "if_statement":
        cond = node.child_by_field_name("condition")
        cons = node.child_by_field_name("consequence")
        alt = node.child_by_field_name("alternative")
        return IRStmt(
            kind="IF",
            condition=trim(decode_text(source, cond)) if cond else "if",
            body=_block_stmts(cons, source),
            else_body=_block_stmts(alt, source),
            line=line,
        )
    if t == "for_statement" or t == "while_statement":
        body = node.child_by_field_name("body")
        return IRStmt(kind="LOOP", condition=t, body=_block_stmts(body, source), line=line)
    if t == "return_statement":
        return IRStmt(kind="RETURN", line=line)
    if t == "call":
        fn = node.child_by_field_name("function")
        return IRStmt(kind="CALL", target=decode_text(source, fn).strip() if fn else "call", line=line)
    return IRStmt(kind="STATEMENT", label=t, line=line)


def _block_stmts(node, source: bytes) -> tuple[IRStmt, ...]:  # noqa: ANN001
    if node is None:
        return ()
    block = node if node.type == "block" else node
    return tuple(s for ch in block.children if (s := _py_stmt(ch, source)) is not None)


def populate_ir_methods_python_treesitter(fr: FileParseResult, project_root: Path) -> None:
    if fr.parse_backend != "treesitter":
        fr.ir_methods = []
        return
    loaded = python_language()
    if loaded is None:
        fr.ir_methods = []
        return
    lang, _ = loaded
    source = fr.path.read_bytes()
    tree = Parser(lang).parse(source)
    key = rel_key(fr.path, project_root.resolve())
    fp = str(fr.path.resolve())
    out: list[IRMethod] = []
    cls: str | None = None
    for ch in tree.root_node.children:
        if ch.type == "class_definition":
            cn = ch.child_by_field_name("name")
            cls = decode_text(source, cn).strip() if cn else None
            body = ch.child_by_field_name("body")
            if body:
                for fn in body.children:
                    if fn.type != "function_definition":
                        continue
                    name = fn.child_by_field_name("name")
                    if not name:
                        continue
                    mname = decode_text(source, name).strip()
                    mb = fn.child_by_field_name("body")
                    out.append(
                        IRMethod(
                            symbol_id=sid(key, cls, mname),
                            name=mname,
                            file_path=fp,
                            language="python",
                            body=_block_stmts(mb, source),
                        ),
                    )
        elif ch.type == "function_definition":
            name = ch.child_by_field_name("name")
            if not name:
                continue
            mname = decode_text(source, name).strip()
            mb = ch.child_by_field_name("body")
            out.append(
                IRMethod(
                    symbol_id=sid(key, None, mname),
                    name=mname,
                    file_path=fp,
                    language="python",
                    body=_block_stmts(mb, source),
                ),
            )
    fr.ir_methods = out
