from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from md_generator.pipeline.base import MDPipeline
from md_generator.pipeline.registry import ConverterAdapter, ConverterRegistry, ExtractionOutput
from md_generator.pipeline.sanitizer import TracebackSanitizer


def test_traceback_sanitizer_negative_security_checks():
    raw_tb = """
    Traceback (most recent call last):
      File "C:\\Users\\Konica Shah\\app.py", line 42, in connect
        db = connect(password="secret123", token="Bearer token123")
      File "/home/ubuntu/app/env.py", line 10
        AWS_SECRET_ACCESS_KEY = "aws_secret_key_456"
    Exception: Connection failed
    """

    sanitized = TracebackSanitizer.sanitize(raw_tb)

    # Assert secret values are absent
    assert "secret123" not in sanitized
    assert "token123" not in sanitized
    assert "aws_secret_key_456" not in sanitized
    assert "Konica Shah" not in sanitized
    assert "ubuntu" not in sanitized

    # Assert redaction tags are present
    assert "[REDACTED]" in sanitized


class FailingAdapter:
    def supports(self, source_type: str) -> bool:
        return True

    def extract(self, source_path: str) -> ExtractionOutput:
        if "corrupt" in source_path:
            raise RuntimeError("Corrupt file encountered with password=my_secret_token!")
        return ExtractionOutput(
            raw_markdown="Valid content",
            source_uri=Path(source_path).as_uri(),
            source_type="text.plain",
        )


def test_partial_failure_isolation():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        valid1 = root / "valid1.txt"
        corrupt = root / "corrupt.txt"
        valid2 = root / "valid2.txt"

        valid1.write_text("v1", encoding="utf-8")
        corrupt.write_text("bad", encoding="utf-8")
        valid2.write_text("v2", encoding="utf-8")

        registry = ConverterRegistry()
        registry.register("text.plain", FailingAdapter(), extensions={".txt"})

        pipeline = MDPipeline(registry=registry)
        result = pipeline.process_directory(str(root))

        # Assert valid files completed, corrupt file failed cleanly
        assert len(result.documents) == 2
        assert len(result.errors) == 1
        assert result.statistics.total_discovered == 3
        assert result.statistics.processed_count == 2
        assert result.statistics.failed_count == 1
        assert "corrupt.txt" in result.errors[0].source_uri
        assert "my_secret_token" not in result.errors[0].traceback
