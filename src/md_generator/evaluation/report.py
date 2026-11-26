from __future__ import annotations

"""Benchmark Reporting & Export Utilities.

Phase 2F/Prompt 08 Implementation:
- EvaluationReporter: Generates structured Markdown, CSV, and JSON benchmark reports.
- Includes executive metrics summaries, baseline delta comparisons, and per-sample breakdowns.
"""

import csv
import io
import json
from typing import Any, Dict, List, Optional

from md_generator.evaluation.baseline import RunComparisonResult
from md_generator.evaluation.models import BenchmarkRun


class EvaluationReporter:
    """Generates structured benchmark reports in Markdown, CSV, and JSON formats."""

    @staticmethod
    def generate_markdown_report(
        run: BenchmarkRun,
        comparison: Optional[RunComparisonResult] = None,
    ) -> str:
        """Renders an executive Markdown benchmark evaluation report."""
        lines: List[str] = [
            f"# Benchmark Evaluation Report: `{run.run_id}`",
            "",
            "## 1. Executive Summary",
            "",
            f"- **Dataset ID**: `{run.dataset_id}` ({run.dataset_type.upper()})",
            f"- **Execution Status**: `{run.status.upper()}`",
            f"- **Total Samples Evaluated**: {len(run.sample_results)}",
            f"- **Duration**: {run.duration_seconds:.2f} seconds",
            f"- **Mean Latency**: {run.aggregate_metrics.get('mean_latency_ms', 0.0):.1f} ms/query",
            "",
        ]

        # 2. Aggregate Metrics Table
        lines.extend([
            "## 2. Aggregate Metrics Summary",
            "",
            "| Category | Metric | Score | Target / Direction |",
            "| :--- | :--- | :---: | :--- |",
        ])

        # Retrieval metrics
        retrieval_keys = ["mrr", "map", "context_precision", "context_recall", "ndcg@3", "ndcg@5", "hit_rate@1", "precision@1", "recall@3"]
        for k in retrieval_keys:
            if k in run.aggregate_metrics:
                lines.append(f"| Retrieval | `{k}` | **{run.aggregate_metrics[k]:.4f}** | Higher is better (Max 1.0) |")

        # Answer metrics
        answer_keys = ["faithfulness", "answer_relevance", "evidence_coverage", "context_utilization", "semantic_similarity"]
        for k in answer_keys:
            if k in run.aggregate_metrics:
                lines.append(f"| Answer Quality | `{k}` | **{run.aggregate_metrics[k]:.4f}** | Higher is better (Max 1.0) |")

        # Citation metrics
        citation_keys = ["citation_precision", "citation_recall"]
        for k in citation_keys:
            if k in run.aggregate_metrics:
                lines.append(f"| Citations | `{k}` | **{run.aggregate_metrics[k]:.4f}** | Higher is better (Max 1.0) |")

        lines.append("")

        # 3. Baseline Comparison Table (if provided)
        if comparison is not None:
            lines.extend([
                "## 3. Baseline Comparison & Regression Diff",
                "",
                f"- **Baseline Run ID**: `{comparison.baseline_run_id}`",
                f"- **Summary**: {comparison.summary}",
                f"- **Regression Warning Alert**: {'⚠️ YES (Regressions Detected)' if comparison.has_regressions else '✅ NO (Stable or Improved)'}",
                "",
                "| Metric | Baseline | Current | Delta | Delta % | Status |",
                "| :--- | :---: | :---: | :---: | :---: | :---: |",
            ])
            for m_name, d in comparison.metric_deltas.items():
                status_icon = "🟢" if d.status == "improved" else ("🔴" if d.status == "regressed" else "⚪")
                lines.append(
                    f"| `{m_name}` | {d.baseline_value:.4f} | {d.current_value:.4f} | {d.delta:+.4f} | {d.delta_pct:+.1f}% | {status_icon} {d.status.upper()} |"
                )
            lines.append("")

        # 4. Sample Breakdown Table (Top 10 samples)
        lines.extend([
            "## 4. Sample Evaluation Breakdown",
            "",
            "| Sample ID | Query | Top Chunk | Faithfulness | Relevance | Latency | Status |",
            "| :--- | :--- | :--- | :---: | :---: | :---: | :---: |",
        ])
        for s in run.sample_results[:15]:
            top_c = s.retrieved_chunk_ids[0][:12] if s.retrieved_chunk_ids else "None"
            faith = s.answer_metrics.get("faithfulness", 0.0)
            rel = s.answer_metrics.get("answer_relevance", 0.0)
            status_badge = "✅ OK" if not s.errors else f"❌ {s.errors[0][:15]}"
            clean_q = s.query.replace("|", " ")[:40]
            lines.append(f"| `{s.sample_id}` | {clean_q}... | `{top_c}` | {faith:.2f} | {rel:.2f} | {s.latency_ms:.0f}ms | {status_badge} |")

        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def generate_csv_report(run: BenchmarkRun) -> str:
        """Exports per-sample evaluation metrics to CSV."""
        buf = io.StringIO()
        writer = csv.writer(buf)

        headers = [
            "sample_id",
            "query",
            "retrieved_chunk_count",
            "top_retrieved_chunk",
            "precision@1",
            "recall@3",
            "hit_rate@1",
            "mrr",
            "faithfulness",
            "answer_relevance",
            "citation_precision",
            "latency_ms",
            "has_error",
        ]
        writer.writerow(headers)

        for s in run.sample_results:
            row = [
                s.sample_id,
                s.query,
                len(s.retrieved_chunk_ids),
                s.retrieved_chunk_ids[0] if s.retrieved_chunk_ids else "",
                s.retrieval_metrics.get("precision@1", 0.0),
                s.retrieval_metrics.get("recall@3", 0.0),
                s.retrieval_metrics.get("hit_rate@1", 0.0),
                s.retrieval_metrics.get("mrr", 0.0),
                s.answer_metrics.get("faithfulness", 0.0),
                s.answer_metrics.get("answer_relevance", 0.0),
                s.citation_metrics.get("citation_precision", 0.0),
                round(s.latency_ms, 2),
                bool(s.errors),
            ]
            writer.writerow(row)

        return buf.getvalue()

    @staticmethod
    def generate_json_report(run: BenchmarkRun, indent: int = 2) -> str:
        """Exports full benchmark run in JSON format."""
        return json.dumps(run.to_dict(), indent=indent)
