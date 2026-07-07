from __future__ import annotations

from md_generator.codeflow.adapters.base import (
    ConfigUsage,
    ImportRecord,
    LanguageAdapter,
    ParserBackendRegistry,
    RawDependency,
    RawEvent,
    RawQuery,
    RawResource,
    SymbolRecord,
)
from md_generator.codeflow.adapters.go import GoAdapter
from md_generator.codeflow.adapters.java import JavaAdapter
from md_generator.codeflow.adapters.js_ts import JavaScriptAdapter, TypeScriptAdapter
from md_generator.codeflow.adapters.php import PHPAdapter
from md_generator.codeflow.adapters.python import PythonAdapter
from md_generator.codeflow.adapters.others import (
    KotlinAdapter,
    RustAdapter,
    CSharpAdapter,
    SwiftAdapter,
    RubyAdapter,
    LuaAdapter,
    CAdapter,
    CppAdapter,
)
from md_generator.codeflow.adapters.registry import LanguageAdapterRegistry

# Pre-populated global registry with all adapters
global_registry = LanguageAdapterRegistry()
global_registry.register(JavaAdapter())
global_registry.register(PythonAdapter())
global_registry.register(JavaScriptAdapter())
global_registry.register(TypeScriptAdapter())
global_registry.register(GoAdapter())
global_registry.register(PHPAdapter())
global_registry.register(KotlinAdapter())
global_registry.register(RustAdapter())
global_registry.register(CSharpAdapter())
global_registry.register(SwiftAdapter())
global_registry.register(RubyAdapter())
global_registry.register(LuaAdapter())
global_registry.register(CAdapter())
global_registry.register(CppAdapter())
