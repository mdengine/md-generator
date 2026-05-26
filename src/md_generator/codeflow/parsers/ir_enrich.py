"""Fill ``FileParseResult.ir_methods`` when CFG export is enabled."""

from __future__ import annotations

from pathlib import Path

from md_generator.codeflow.core.run_config import ScanConfig
from md_generator.codeflow.models.ir import FileParseResult
from md_generator.codeflow.parsers.adapters import (
    populate_ir_methods_java,
    populate_ir_methods_python,
)
from md_generator.codeflow.parsers.adapters.cpp_adapter import populate_ir_methods_cpp
from md_generator.codeflow.parsers.adapters.go_adapter import populate_ir_methods_go
from md_generator.codeflow.parsers.adapters.php_adapter import populate_ir_methods_php


def enrich_parse_results_with_ir(results: list[FileParseResult], cfg: ScanConfig, project_root: Path) -> None:
    if not cfg.emit_cfg:
        return
    root = project_root.resolve()
    for fr in results:
        if fr.language == "python":
            if fr.parse_backend == "treesitter":
                from md_generator.codeflow.parsers.adapters.treesitter_python_adapter import (
                    populate_ir_methods_python_treesitter,
                )

                populate_ir_methods_python_treesitter(fr, root)
            else:
                populate_ir_methods_python(fr, root)
        elif fr.language == "java":
            if fr.parse_backend == "treesitter":
                from md_generator.codeflow.parsers.adapters.treesitter_java_adapter import (
                    populate_ir_methods_java_treesitter,
                )

                populate_ir_methods_java_treesitter(fr, root)
            else:
                populate_ir_methods_java(fr, root)
        elif fr.language in ("javascript", "typescript", "tsx"):
            try:
                from md_generator.codeflow.parsers.adapters import populate_ir_methods_treesitter

                populate_ir_methods_treesitter(fr, root)
            except ImportError:
                fr.ir_methods = []
        elif fr.language == "go" and cfg.cfg_ir_go:
            if fr.parse_backend == "treesitter":
                from md_generator.codeflow.parsers.adapters.treesitter_go_adapter import (
                    populate_ir_methods_go_treesitter,
                )

                populate_ir_methods_go_treesitter(fr, root)
            else:
                populate_ir_methods_go(fr)
        elif fr.language == "php" and cfg.cfg_ir_php:
            if fr.parse_backend == "treesitter":
                from md_generator.codeflow.parsers.adapters.treesitter_php_adapter import (
                    populate_ir_methods_php_treesitter,
                )

                populate_ir_methods_php_treesitter(fr, root)
            else:
                populate_ir_methods_php(fr)
        elif fr.language == "cpp" and cfg.cfg_ir_cpp:
            populate_ir_methods_cpp(fr, root)
        elif fr.language == "rust" and fr.parse_backend == "treesitter":
            from md_generator.codeflow.parsers.adapters.treesitter_rust_adapter import (
                populate_ir_methods_rust_treesitter,
            )

            populate_ir_methods_rust_treesitter(fr, root)
        elif fr.language == "kotlin" and fr.parse_backend == "treesitter":
            from md_generator.codeflow.parsers.adapters.treesitter_kotlin_adapter import (
                populate_ir_methods_kotlin_treesitter,
            )

            populate_ir_methods_kotlin_treesitter(fr, root)
        elif fr.language == "csharp" and fr.parse_backend == "treesitter":
            from md_generator.codeflow.parsers.adapters.treesitter_csharp_adapter import (
                populate_ir_methods_csharp_treesitter,
            )

            populate_ir_methods_csharp_treesitter(fr, root)
        elif fr.language == "swift" and fr.parse_backend == "treesitter":
            from md_generator.codeflow.parsers.adapters.treesitter_swift_adapter import (
                populate_ir_methods_swift_treesitter,
            )

            populate_ir_methods_swift_treesitter(fr, root)
        elif fr.language == "ruby" and fr.parse_backend == "treesitter":
            from md_generator.codeflow.parsers.adapters.treesitter_ruby_adapter import (
                populate_ir_methods_ruby_treesitter,
            )

            populate_ir_methods_ruby_treesitter(fr, root)
        elif fr.language == "lua" and fr.parse_backend == "treesitter":
            from md_generator.codeflow.parsers.adapters.treesitter_lua_adapter import (
                populate_ir_methods_lua_treesitter,
            )

            populate_ir_methods_lua_treesitter(fr, root)
        elif fr.language == "scala" and fr.parse_backend == "treesitter":
            from md_generator.codeflow.parsers.adapters.treesitter_scala_adapter import (
                populate_ir_methods_scala_treesitter,
            )

            populate_ir_methods_scala_treesitter(fr, root)
        elif fr.language == "zig" and fr.parse_backend == "treesitter":
            from md_generator.codeflow.parsers.adapters.treesitter_zig_adapter import (
                populate_ir_methods_zig_treesitter,
            )

            populate_ir_methods_zig_treesitter(fr, root)
        else:
            fr.ir_methods = []
