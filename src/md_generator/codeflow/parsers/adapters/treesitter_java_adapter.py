"""Tree-sitter Java method bodies → IRMethod / IRStmt."""

from __future__ import annotations

from pathlib import Path

from tree_sitter import Parser

from md_generator.codeflow.models.ir import FileParseResult
from md_generator.codeflow.models.ir_cfg import IRMethod, IRStmt
from md_generator.codeflow.parsers.treesitter_common import decode_text, rel_key, sid, trim
from md_generator.codeflow.parsers.treesitter_java_parser import java_language


def _stmt_list_from_block(block, source: bytes) -> tuple[IRStmt, ...]:  # noqa: ANN001
    if block is None:
        return ()
    out: list[IRStmt] = []
    for ch in getattr(block, "children", []) or []:
        ir = _java_ts_stmt(ch, source)
        if ir is not None:
            out.append(ir)
    return tuple(out)


def _java_ts_stmt(node, source: bytes) -> IRStmt | None:  # noqa: ANN001
    t = node.type
    line = node.start_point[0] + 1
    if t == "if_statement":
        cond = node.child_by_field_name("condition")
        cons = node.child_by_field_name("consequence")
        alt = node.child_by_field_name("alternative")
        then_body = _stmt_list_from_block(cons, source) if cons and cons.type == "block" else ()
        else_body = _stmt_list_from_block(alt, source) if alt and alt.type == "block" else ()
        return IRStmt(
            kind="IF",
            condition=trim(decode_text(source, cond)) if cond else "if",
            body=then_body,
            else_body=else_body,
            line=line,
        )
    if t in ("while_statement", "for_statement", "enhanced_for_statement"):
        cond = node.child_by_field_name("condition")
        body = node.child_by_field_name("body")
        return IRStmt(
            kind="LOOP",
            condition=trim(decode_text(source, cond)) if cond else t,
            body=_stmt_list_from_block(body, source),
            line=line,
        )
    if t == "try_statement":
        body = node.child_by_field_name("body")
        return IRStmt(kind="TRY", body=_stmt_list_from_block(body, source), line=line)
    if t == "return_statement":
        val = node.child_by_field_name("value")
        return IRStmt(kind="RETURN", label=trim(decode_text(source, val)) if val else "return", line=line)
    if t == "break_statement":
        return IRStmt(kind="BREAK", line=line)
    if t == "continue_statement":
        return IRStmt(kind="CONTINUE", line=line)
    if t == "method_invocation":
        name = node.child_by_field_name("name")
        return IRStmt(kind="CALL", target=decode_text(source, name).strip() if name else "call", line=line)
    if t == "block":
        inner = _stmt_list_from_block(node, source)
        if len(inner) == 1:
            return inner[0]
        if inner:
            return IRStmt(kind="STATEMENT", label="block", body=inner, line=line)
    return IRStmt(kind="STATEMENT", label=t, line=line)


def populate_ir_methods_java_treesitter(fr: FileParseResult, project_root: Path) -> None:
    if fr.parse_backend != "treesitter" or not str(fr.path).endswith(".java"):
        fr.ir_methods = []
        return
    loaded = java_language()
    if loaded is None:
        fr.ir_methods = []
        return
    lang, _ = loaded
    source = fr.path.read_bytes()
    tree = Parser(lang).parse(source)
    key = rel_key(fr.path, project_root.resolve())
    fp = str(fr.path.resolve())
    out: list[IRMethod] = []

    def parse_type(node, prefix: tuple[str, ...]) -> None:  # noqa: ANN001
        name_n = node.child_by_field_name("name")
        if not name_n:
            return
        parts = prefix + (decode_text(source, name_n).strip(),)
        fq = ".".join(parts)
        body = node.child_by_field_name("body")
        if not body:
            return
        for ch in body.children:
            if ch.type == "method_declaration":
                mn = ch.child_by_field_name("name")
                if not mn:
                    continue
                mname = decode_text(source, mn).strip()
                mb = ch.child_by_field_name("body")
                body_ir = _stmt_list_from_block(mb, source) if mb else ()
                out.append(
                    IRMethod(
                        symbol_id=sid(key, fq, mname),
                        name=mname,
                        file_path=fp,
                        language="java",
                        body=body_ir,
                    ),
                )
            elif ch.type in ("class_declaration", "interface_declaration", "enum_declaration"):
                parse_type(ch, parts)

    for ch in tree.root_node.children:
        if ch.type in ("class_declaration", "interface_declaration", "enum_declaration"):
            parse_type(ch, ())
    fr.ir_methods = out
