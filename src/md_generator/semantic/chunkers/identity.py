"""Symbol identity representation and language-aware FQN generation.

Defines SymbolIdentity, controlled entity/relationship taxonomies,
and qualification strategies for canonical semantic key computation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Set


class EntityType(str, Enum):
    """Controlled taxonomy for extracted structural entities."""
    MODULE = "MODULE"
    PACKAGE = "PACKAGE"
    NAMESPACE = "NAMESPACE"
    CLASS = "CLASS"
    INTERFACE = "INTERFACE"
    STRUCT = "STRUCT"
    ENUM = "ENUM"
    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    ENDPOINT = "ENDPOINT"
    SCHEMA = "SCHEMA"
    TABLE = "TABLE"
    VIEW = "VIEW"
    COLUMN = "COLUMN"
    SAP_OBJECT = "SAP_OBJECT"


class RelationshipType(str, Enum):
    """Controlled taxonomy for extracted structural relationships."""
    DEFINES = "DEFINES"
    CONTAINS = "CONTAINS"
    CALLS = "CALLS"
    IMPORTS = "IMPORTS"
    INHERITS = "INHERITS"
    IMPLEMENTS = "IMPLEMENTS"
    OVERRIDES = "OVERRIDES"
    REFERENCES = "REFERENCES"
    USES_TYPE = "USES_TYPE"
    EXPOSES = "EXPOSES"
    CONSUMES = "CONSUMES"
    DEPENDS_ON = "DEPENDS_ON"
    MAPS_TO = "MAPS_TO"


VALID_ENTITY_TYPES: Set[str] = {e.value for e in EntityType}
VALID_RELATIONSHIP_TYPES: Set[str] = {r.value for r in RelationshipType}


@dataclass
class SymbolIdentity:
    """Represents a language-aware structural symbol and its Fully Qualified Name (FQN)."""

    language: str
    symbol_kind: str                                    # 'class', 'method', 'function', 'struct', 'table', 'endpoint'
    local_name: str
    qualified_name: str                                 # Language-specific FQN
    parent_symbol: Optional[str] = None
    qualification_strategy: str = "default"

    def compute_semantic_key(self) -> str:
        """Format canonical semantic key (e.g. class:com.company.PaymentService)."""
        kind = self.symbol_kind.strip().lower()
        fqn = self.qualified_name.strip()
        return f"{kind}:{fqn}"


def compute_fqn(
    language: str,
    symbol_kind: str,
    local_name: str,
    parent_symbol: Optional[str] = None,
    namespace: Optional[str] = None,
) -> SymbolIdentity:
    """Compute a language-aware SymbolIdentity according to language qualification contracts."""
    lang = language.strip().lower()
    local = local_name.strip()
    parent = parent_symbol.strip() if parent_symbol else None
    ns = namespace.strip() if namespace else None

    if lang in ("python", "py"):
        # Python: module.Class.method
        parts = [p for p in (ns, parent, local) if p]
        fqn = ".".join(parts)
        strategy = "python_module_qualified"
    elif lang == "java":
        # Java: package.Class.method
        parts = [p for p in (ns, parent, local) if p]
        fqn = ".".join(parts)
        strategy = "java_package_qualified"
    elif lang in ("typescript", "javascript", "ts", "js", "tsx", "jsx"):
        # TypeScript/JS: module/export.Class.method
        if ns and parent:
            fqn = f"{ns}.{parent}.{local}"
        elif ns:
            fqn = f"{ns}.{local}"
        elif parent:
            fqn = f"{parent}.{local}"
        else:
            fqn = local
        strategy = "ts_module_export_qualified"
    elif lang in ("go", "golang"):
        # Go: package.Type.Method
        parts = [p for p in (ns, parent, local) if p]
        fqn = ".".join(parts)
        strategy = "go_package_qualified"
    elif lang in ("cpp", "c++", "c"):
        # C/C++: namespace::Class::method
        parts = [p for p in (ns, parent, local) if p]
        fqn = "::".join(parts)
        strategy = "cpp_namespace_qualified"
    elif lang in ("csharp", "c#", "cs"):
        # C#: Namespace.Type.Method
        parts = [p for p in (ns, parent, local) if p]
        fqn = ".".join(parts)
        strategy = "csharp_namespace_qualified"
    else:
        # Generic fallback: parent.local or local
        parts = [p for p in (ns, parent, local) if p]
        fqn = ".".join(parts)
        strategy = "generic_dot_qualified"

    return SymbolIdentity(
        language=language,
        symbol_kind=symbol_kind,
        local_name=local,
        qualified_name=fqn,
        parent_symbol=parent,
        qualification_strategy=strategy,
    )
