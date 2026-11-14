from __future__ import annotations

import hashlib
from pathlib import Path
import pytest

from md_generator.lineage.ids import compute_file_content_hash, compute_content_hash


def test_binary_hashing_deterministic(tmp_path: Path):
    file1 = tmp_path / "test1.bin"
    file2 = tmp_path / "test2.bin"
    payload = b"\x00\xFF\xFE\xFD\x80\x81\xC0\xC1\x00\x00BinaryData"
    file1.write_bytes(payload)
    file2.write_bytes(payload)

    hash1 = compute_file_content_hash(file1)
    hash2 = compute_file_content_hash(file2)
    expected = hashlib.sha256(payload).hexdigest()

    assert hash1 == expected
    assert hash2 == expected
    assert hash1 == hash2


def test_binary_hashing_single_byte_diff(tmp_path: Path):
    file1 = tmp_path / "f1.bin"
    file2 = tmp_path / "f2.bin"
    payload1 = b"abc\x00\xFFxyz"
    payload2 = b"abc\x01\xFFxyz"
    file1.write_bytes(payload1)
    file2.write_bytes(payload2)

    assert compute_file_content_hash(file1) != compute_file_content_hash(file2)


def test_empty_file_hashing(tmp_path: Path):
    empty_file = tmp_path / "empty.bin"
    empty_file.write_bytes(b"")

    empty_hash = compute_file_content_hash(empty_file)
    expected_empty_sha256 = hashlib.sha256(b"").hexdigest()
    assert empty_hash == expected_empty_sha256
    assert empty_hash == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_missing_file_raises_error(tmp_path: Path):
    missing_file = tmp_path / "non_existent.bin"
    with pytest.raises(FileNotFoundError):
        compute_file_content_hash(missing_file)


def test_directory_path_raises_error(tmp_path: Path):
    subdir = tmp_path / "somedir"
    subdir.mkdir()
    with pytest.raises(IsADirectoryError):
        compute_file_content_hash(subdir)


def test_legacy_text_hash_preserved():
    text = "Hello world"
    expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert compute_content_hash(text) == expected

