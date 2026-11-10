from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from md_generator.pipeline.registry import (
    BaseTextAdapter,
    CodeflowAdapter,
    ConverterRegistry,
    UnsupportedSourceError,
)


def test_converter_registry_explicit_source_type():
    registry = ConverterRegistry.create_default()
    adapter = registry.resolve("some_file.txt", source_type="code.python")
    assert isinstance(adapter, CodeflowAdapter)
    assert adapter.lang_key == "python"


def test_converter_registry_exact_filename_precedence():
    registry = ConverterRegistry.create_default()
    adapter = registry.resolve("swagger.openapi.json")
    assert adapter._source_type == "api.openapi"


def test_converter_registry_codeflow_extension_mapping():
    registry = ConverterRegistry.create_default()

    extensions = [
        ("test.py", "python"),
        ("App.java", "java"),
        ("index.js", "javascript"),
        ("component.tsx", "tsx"),
        ("main.go", "go"),
        ("lib.rs", "rust"),
        ("script.kt", "kotlin"),
        ("Program.cs", "csharp"),
        ("main.cpp", "cpp"),
    ]

    for filename, expected_lang in extensions:
        adapter = registry.resolve(filename)
        assert isinstance(adapter, CodeflowAdapter)
        assert adapter.lang_key == expected_lang


def test_converter_registry_unsupported_source_error():
    registry = ConverterRegistry()  # Empty registry
    with pytest.raises(UnsupportedSourceError):
        registry.resolve("file.unknown_extension")
