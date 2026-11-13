from __future__ import annotations

from pathlib import Path
import pytest

from md_generator.pipeline.registry import (
    BaseTextAdapter,
    ConverterRegistry,
    PDFConverterAdapter,
    WordConverterAdapter,
    PPTConverterAdapter,
    ExcelConverterAdapter,
    MissingDependencyError,
    UnsupportedSourceError,
)


def test_registry_resolves_specialized_adapters():
    registry = ConverterRegistry.create_default()

    pdf_adapter = registry.resolve("doc.pdf")
    assert isinstance(pdf_adapter, PDFConverterAdapter)
    assert not isinstance(pdf_adapter, BaseTextAdapter)

    word_adapter = registry.resolve("document.docx")
    assert isinstance(word_adapter, WordConverterAdapter)
    assert not isinstance(word_adapter, BaseTextAdapter)

    ppt_adapter = registry.resolve("slides.pptx")
    assert isinstance(ppt_adapter, PPTConverterAdapter)
    assert not isinstance(ppt_adapter, BaseTextAdapter)

    xlsx_adapter = registry.resolve("data.xlsx")
    assert isinstance(xlsx_adapter, ExcelConverterAdapter)
    assert not isinstance(xlsx_adapter, BaseTextAdapter)


def test_pdf_adapter_with_real_fixture():
    fixture_path = Path("pdf-to-md/tests/fixtures/minimal.pdf").resolve()
    if not fixture_path.exists():
        pytest.skip("minimal.pdf fixture not found")

    adapter = PDFConverterAdapter()
    output = adapter.extract(str(fixture_path))
    assert output.source_type == "doc.pdf"
    assert "\uFFFD" not in output.raw_markdown
    assert len(output.raw_markdown.strip()) > 0


def test_ppt_adapter_with_real_fixture():
    fixture_path = Path("ppt-to-md/tests/fixtures/minimal.pptx").resolve()
    if not fixture_path.exists():
        pytest.skip("minimal.pptx fixture not found")

    adapter = PPTConverterAdapter()
    output = adapter.extract(str(fixture_path))
    assert output.source_type == "doc.ppt"
    assert "\uFFFD" not in output.raw_markdown


def test_pdf_adapter_fail_closed_on_corrupt_binary(tmp_path: Path):
    corrupt_pdf = tmp_path / "corrupt.pdf"
    corrupt_pdf.write_bytes(b"\x00\xFF\xFE\x00NotAPdfHeader")

    adapter = PDFConverterAdapter()
    with pytest.raises((UnsupportedSourceError, MissingDependencyError)):
        adapter.extract(str(corrupt_pdf))


def test_word_adapter_fail_closed_on_corrupt_binary(tmp_path: Path):
    corrupt_word = tmp_path / "corrupt.docx"
    corrupt_word.write_bytes(b"PK\x00\x00CorruptZipStream")

    adapter = WordConverterAdapter()
    with pytest.raises((UnsupportedSourceError, MissingDependencyError)):
        adapter.extract(str(corrupt_word))


def test_excel_adapter_fail_closed_on_corrupt_binary(tmp_path: Path):
    corrupt_xlsx = tmp_path / "corrupt.xlsx"
    corrupt_xlsx.write_bytes(b"PK\x03\x04CorruptExcelData")

    adapter = ExcelConverterAdapter()
    with pytest.raises((UnsupportedSourceError, MissingDependencyError)):
        adapter.extract(str(corrupt_xlsx))

