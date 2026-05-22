"""Tree-sitter PHP → IRMethod (minimal)."""

from __future__ import annotations

from pathlib import Path

from tree_sitter import Parser

from md_generator.codeflow.models.ir import FileParseResult
from md_generator.codeflow.models.ir_cfg import IRMethod, IRStmt
from md_generator.codeflow.parsers.treesitter_common import decode_text, rel_key, sid
from md_generator.codeflow.parsers.treesitter_php_parser import php_language


def populate_ir_methods_php_treesitter(fr: FileParseResult, project_root: Path) -> None:
    if fr.parse_backend != "treesitter":
        fr.ir_methods = []
        return
    loaded = php_language()
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
        if ch.type == "class_declaration":
            cn = ch.child_by_field_name("name")
            cls = decode_text(source, cn).strip() if cn else None
            body = ch.child_by_field_name("body")
            if body:
                for m in body.children:
                    if m.type != "method_declaration":
                        continue
                    mn = m.child_by_field_name("name")
                    if not mn:
                        continue
                    mname = decode_text(source, mn).strip()
                    out.append(
                        IRMethod(
                            symbol_id=sid(key, cls, mname),
                            name=mname,
                            file_path=fp,
                            language="php",
                            body=(),
                        ),
                    )
        elif ch.type == "function_definition":
            mn = ch.child_by_field_name("name")
            if mn:
                mname = decode_text(source, mn).strip()
                out.append(
                    IRMethod(
                        symbol_id=sid(key, None, mname),
                        name=mname,
                        file_path=fp,
                        language="php",
                        body=(),
                    ),
                )
    fr.ir_methods = out
