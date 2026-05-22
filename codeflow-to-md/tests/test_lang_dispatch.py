from __future__ import annotations

from pathlib import Path

from md_generator.codeflow.lang_dispatch import (
    extensions_for_languages,
    lang_for_path,
    normalize_language_filter,
    should_parse_file_lang,
)


def test_normalize_mixed_includes_js() -> None:
    exts = extensions_for_languages(normalize_language_filter("mixed"))
    assert ".ts" in exts
    assert ".go" in exts


def test_lang_for_path() -> None:
    assert lang_for_path(Path("a.tsx")) == "tsx"
    assert lang_for_path(Path("b.go")) == "go"
    assert lang_for_path(Path("lib.rs")) == "rust"
    assert lang_for_path(Path("Main.kt")) == "kotlin"
    assert lang_for_path(Path("App.kts")) == "kotlin"
    assert lang_for_path(Path("Program.cs")) == "csharp"


def test_normalize_rust_kotlin_csharp_aliases() -> None:
    assert normalize_language_filter("rs") == frozenset({"rust"})
    assert normalize_language_filter("kt") == frozenset({"kotlin"})
    assert normalize_language_filter("cs") == frozenset({"csharp"})
    assert normalize_language_filter("c#") == frozenset({"csharp"})


def test_should_parse_filter() -> None:
    allowed = normalize_language_filter("python,javascript")
    assert should_parse_file_lang("python", allowed)
    assert should_parse_file_lang("javascript", allowed)
    assert not should_parse_file_lang("go", allowed)
