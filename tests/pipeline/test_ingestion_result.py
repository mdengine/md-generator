from __future__ import annotations

import pytest

from md_generator.pipeline.result import (
    IngestionError,
    IngestionResult,
    IngestionStatistics,
    compute_execution_fingerprint,
)


def test_ingestion_result_run_id_unique_per_instance():
    res1 = IngestionResult()
    res2 = IngestionResult()
    assert res1.run_id != res2.run_id
    assert len(res1.run_id) == 32  # UUID4 hex string


def test_compute_execution_fingerprint_determinism():
    config_fp = "a" * 64
    docs = [
        {"document_id": "doc_1", "revision_id": "rev_1"},
        {"document_id": "doc_2", "revision_id": "rev_2"},
    ]

    fp1 = compute_execution_fingerprint(config_fp, "process_file", "file:///test.py", docs)
    fp2 = compute_execution_fingerprint(config_fp, "process_file", "file:///test.py", list(reversed(docs)))

    assert fp1 == fp2
    assert len(fp1) == 64


def test_ingestion_result_to_dict():
    res = IngestionResult(
        execution_fingerprint="exec_123",
        config_fingerprint="cfg_123",
        statistics=IngestionStatistics(total_discovered=5, processed_count=5),
    )
    d = res.to_dict()
    assert d["run_id"] == res.run_id
    assert d["execution_fingerprint"] == "exec_123"
    assert d["config_fingerprint"] == "cfg_123"
    assert d["statistics"]["total_discovered"] == 5
    assert d["statistics"]["processed_count"] == 5
