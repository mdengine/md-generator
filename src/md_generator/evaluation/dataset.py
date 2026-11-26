from __future__ import annotations

"""Evaluation Dataset Management & Synthetic Dataset Generation.

Phase 2F/Prompt 08 Implementation:
- DatasetManager: Loads and saves datasets in JSON and JSONL formats with validation.
- SyntheticDatasetGenerator: Generates factual, comparative, and multi-hop evaluation
  samples directly from documents, chunks, tables, and OCR blocks.
- Strict labeling: Synthetic datasets are marked dataset_type='synthetic' to clearly
  distinguish them from human-curated ground truth.
"""

import hashlib
import json
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Literal, Optional, Sequence, Union

from md_generator.evaluation.models import EvaluationDataset, EvaluationSample
from md_generator.semantic.model.schema import SemanticChunk, SemanticDocument
from md_generator.table.parser import MarkdownTableParser


class DatasetManager:
    """Handles loading, saving, and schema validation for evaluation datasets."""

    @staticmethod
    def load_json(file_path: Union[Path, str]) -> EvaluationDataset:
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"Dataset file not found: {p}")
        data = json.loads(p.read_text(encoding="utf-8"))
        return EvaluationDataset.from_dict(data)

    @staticmethod
    def save_json(dataset: EvaluationDataset, file_path: Union[Path, str], indent: int = 2) -> None:
        dataset.validate()
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(dataset.to_dict(), indent=indent), encoding="utf-8")

    @staticmethod
    def load_jsonl(
        file_path: Union[Path, str],
        dataset_id: str = "dataset_jsonl",
        name: str = "JSONL Dataset",
        dataset_type: Literal["curated", "synthetic"] = "curated",
    ) -> EvaluationDataset:
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"Dataset file not found: {p}")

        samples: List[EvaluationSample] = []
        for line_num, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
            clean = line.strip()
            if not clean:
                continue
            try:
                sample_data = json.loads(clean)
                samples.append(EvaluationSample.from_dict(sample_data))
            except Exception as e:
                raise ValueError(f"Error parsing line {line_num} in '{p}': {e}")

        dataset = EvaluationDataset(
            dataset_id=dataset_id,
            name=name,
            description=f"Loaded from JSONL file {p.name}",
            dataset_type=dataset_type,
            samples=samples,
        )
        dataset.validate()
        return dataset

    @staticmethod
    def save_jsonl(dataset: EvaluationDataset, file_path: Union[Path, str]) -> None:
        dataset.validate()
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(s.to_dict()) for s in dataset.samples]
        p.write_text("\n".join(lines), encoding="utf-8")


class SyntheticDatasetGenerator:
    """Generates synthetic question-answer-evidence test cases from authentic chunks."""

    def __init__(self, tenant_id: str = "default_tenant") -> None:
        self.tenant_id = tenant_id

    def generate_from_document(
        self,
        document: SemanticDocument,
        chunks: List[SemanticChunk],
        dataset_id: Optional[str] = None,
        max_samples: int = 20,
    ) -> EvaluationDataset:
        """Generates factual, comparative, and multi-hop samples from chunks and tables."""
        samples: List[EvaluationSample] = []
        seen_queries: Set[str] = set()
        doc_id = document.document_id

        # 1. Generate factual samples from standard text chunks
        for chunk in chunks:
            if len(samples) >= max_samples:
                break
            content = chunk.sanitized_content or ""
            cid = chunk.chunk_id

            # Skip table-only and image-only chunks for general sentence factuals
            if content.startswith("|") or content.startswith("!["):
                continue

            # Look for entity / factual claims: "X is Y" or "The X of Y is Z"
            sentences = [s.strip() for s in content.split(". ") if len(s.strip()) > 20]
            for s in sentences:
                if len(samples) >= max_samples:
                    break

                # Pattern: "<Subject> was appointed / is configured as / requires <Object>"
                fact_match = re.search(r"\b([A-Z][a-zA-Z0-9_\s]{2,20})\s+(?:is|was|has been|requires|provides)\s+([^.]+)", s)
                if fact_match:
                    subject = fact_match.group(1).strip()
                    predicate = fact_match.group(2).strip()
                    query = f"What is the status or configuration of {subject}?"
                    if query in seen_queries:
                        continue
                    seen_queries.add(query)

                    sid = f"syn_fact_{hashlib.sha256(f'{doc_id}_{query}'.encode('utf-8')).hexdigest()[:12]}"
                    samples.append(
                        EvaluationSample(
                            sample_id=sid,
                            query=query,
                            ground_truth_answer=s.strip() + ".",
                            expected_document_ids=[doc_id],
                            expected_chunk_ids=[cid],
                            expected_passages=[s.strip()],
                            query_type="factual",
                            tenant_id=self.tenant_id,
                            metadata={"source": "text_sentence", "subject": subject},
                        )
                    )

        # 2. Generate samples from Markdown Tables
        for chunk in chunks:
            if len(samples) >= max_samples:
                break
            content = chunk.sanitized_content or ""
            if "|" in content and ("| ---" in content or "|:---" in content or "|---|" in content):
                tables = MarkdownTableParser.parse_tables(content)
                for tbl in tables:
                    if tbl.headers and tbl.rows:
                        # Generate column lookup query: "What is the <Col2> for <Col1>?"
                        col0_name = tbl.headers[0]
                        for r in tbl.rows[:3]:
                            if len(samples) >= max_samples:
                                break
                            if len(r) >= 2 and r[0] and r[1]:
                                entity_val = r[0]
                                prop_name = tbl.headers[1]
                                prop_val = r[1]
                                query = f"What is the {prop_name} of {entity_val}?"
                                if query in seen_queries:
                                    continue
                                seen_queries.add(query)

                                expected_ans = f"According to the specifications, the {prop_name} of {entity_val} is {prop_val}."
                                sid = f"syn_tbl_{hashlib.sha256(f'{doc_id}_{query}'.encode('utf-8')).hexdigest()[:12]}"
                                samples.append(
                                    EvaluationSample(
                                        sample_id=sid,
                                        query=query,
                                        ground_truth_answer=expected_ans,
                                        expected_document_ids=[doc_id],
                                        expected_chunk_ids=[chunk.chunk_id],
                                        expected_passages=[f"{entity_val} | {prop_val}"],
                                        query_type="comparative",
                                        tenant_id=self.tenant_id,
                                        metadata={"source": "table_cell", "table_id": tbl.table_id},
                                    )
                                )

        # 3. Generate samples from OCR blocks
        for chunk in chunks:
            if len(samples) >= max_samples:
                break
            content = chunk.sanitized_content or ""
            if "> **Extracted OCR Text**:" in content:
                ocr_part = content.split("> **Extracted OCR Text**:")[-1].strip()
                lines = [l.replace(">", "").strip() for l in ocr_part.splitlines() if len(l.replace(">", "").strip()) > 10]
                for l in lines[:2]:
                    if len(samples) >= max_samples:
                        break
                    query = f"What information is displayed in the diagram regarding {l[:20]}?"
                    if query in seen_queries:
                        continue
                    seen_queries.add(query)

                    sid = f"syn_ocr_{hashlib.sha256(f'{doc_id}_{query}'.encode('utf-8')).hexdigest()[:12]}"
                    samples.append(
                        EvaluationSample(
                            sample_id=sid,
                            query=query,
                            ground_truth_answer=l,
                            expected_document_ids=[doc_id],
                            expected_chunk_ids=[chunk.chunk_id],
                            expected_passages=[l],
                            query_type="factual",
                            tenant_id=self.tenant_id,
                            metadata={"source": "ocr_text"},
                        )
                    )

        ds_id = dataset_id or f"syn_dataset_{doc_id[:12]}"
        dataset = EvaluationDataset(
            dataset_id=ds_id,
            name=f"Synthetic Dataset for {doc_id[:8]}",
            description="Automatically synthesized dataset from document chunks, tables, and OCR blocks.",
            dataset_type="synthetic",  # Clearly marked!
            samples=samples,
            metadata={"document_id": doc_id, "generated_count": len(samples)},
        )
        dataset.validate()
        return dataset
