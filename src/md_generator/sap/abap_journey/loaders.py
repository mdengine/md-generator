from __future__ import annotations

from pathlib import Path
from md_generator.sap.canonical.base import CanonicalArtifact
from md_generator.sap.parser.abap.lexer import iter_statements

class SourceLoader:
    def __init__(self, artifacts: dict[str, CanonicalArtifact]) -> None:
        self.artifacts = {k.upper(): v for k, v in artifacts.items()}

    def load_source(self, name: str, parent_path: Path | None = None) -> tuple[str, Path] | None:
        name_upper = name.upper()
        # 1. Lookup in artifacts
        artifact = self.artifacts.get(name_upper)
        if artifact and artifact.source_path:
            path = Path(artifact.source_path)
            if path.exists():
                try:
                    return path.read_text(encoding="utf-8", errors="replace"), path
                except Exception:
                    pass

        # 2. Fallback to same directory as parent_path
        if parent_path:
            parent_dir = parent_path.parent
            for ext in (".abap", ".prog", ".asprog", ".inc"):
                for filename in (name_upper.lower() + ext, name_upper + ext):
                    candidate = parent_dir / filename
                    if candidate.exists():
                        try:
                            return candidate.read_text(encoding="utf-8", errors="replace"), candidate
                        except Exception:
                            pass
        return None

class StatementCache:
    def __init__(self) -> None:
        self._cache: dict[Path, list[tuple[int, str]]] = {}

    def get_statements(self, path: Path, source_content: str | None = None) -> list[tuple[int, str]]:
        if path in self._cache:
            return self._cache[path]
        
        content = source_content
        if content is None:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                content = ""
                
        stmts = iter_statements(content)
        self._cache[path] = stmts
        return stmts
