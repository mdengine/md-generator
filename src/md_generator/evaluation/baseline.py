from __future__ import annotations

"""Baseline Management & Regression Comparison Engine.

Phase 2F/Prompt 08 Implementation:
- Compares current benchmark runs against historical baselines.
- Calculates metric-by-metric deltas: delta = current - baseline.
- Detects quality regressions exceeding configurable warning thresholds.
- Detects quality improvements and stability indicators.
- Persists and loads baseline files.
"""

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from md_generator.evaluation.models import BenchmarkRun


@dataclass
class MetricDelta:
    """Represents change in a specific evaluation metric."""
    metric_name: str
    baseline_value: float
    current_value: float
    delta: float                          # current - baseline
    delta_pct: float                      # percentage change
    status: str                           # "improved", "regressed", "unchanged"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "baseline_value": self.baseline_value,
            "current_value": self.current_value,
            "delta": round(self.delta, 4),
            "delta_pct": round(self.delta_pct, 2),
            "status": self.status,
        }


@dataclass
class RunComparisonResult:
    """Comparison report between a current benchmark run and a baseline run."""
    current_run_id: str
    baseline_run_id: str
    dataset_id: str
    metric_deltas: Dict[str, MetricDelta]
    regressions_count: int
    improvements_count: int
    has_regressions: bool
    warning_threshold_pct: float
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_run_id": self.current_run_id,
            "baseline_run_id": self.baseline_run_id,
            "dataset_id": self.dataset_id,
            "warning_threshold_pct": self.warning_threshold_pct,
            "has_regressions": self.has_regressions,
            "regressions_count": self.regressions_count,
            "improvements_count": self.improvements_count,
            "summary": self.summary,
            "metric_deltas": {k: v.to_dict() for k, v in self.metric_deltas.items()},
        }


class BaselineManager:
    """Manages baseline persistence and regression diff analysis."""

    @staticmethod
    def save_baseline(run: BenchmarkRun, file_path: Union[Path, str]) -> None:
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(run.to_dict(), indent=2), encoding="utf-8")

    @staticmethod
    def load_baseline(file_path: Union[Path, str]) -> BenchmarkRun:
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"Baseline run file not found: {p}")
        data = json.loads(p.read_text(encoding="utf-8"))
        return BenchmarkRun.from_dict(data)

    @staticmethod
    def compare_runs(
        current_run: BenchmarkRun,
        baseline_run: BenchmarkRun,
        warning_threshold_pct: float = 5.0,  # e.g., 5.0% drop triggers warning
    ) -> RunComparisonResult:
        """Compares current run metrics against baseline run metrics."""
        deltas: Dict[str, MetricDelta] = {}
        regressions = 0
        improvements = 0

        curr_metrics = current_run.aggregate_metrics
        base_metrics = baseline_run.aggregate_metrics

        all_keys = sorted(list(set(curr_metrics.keys()).union(set(base_metrics.keys()))))

        for key in all_keys:
            # Skip latency from standard positive metric logic (for latency, higher is worse)
            if key == "mean_latency_ms":
                continue

            c_val = curr_metrics.get(key, 0.0)
            b_val = base_metrics.get(key, 0.0)
            diff = c_val - b_val

            if b_val > 0.0:
                pct = (diff / b_val) * 100.0
            else:
                pct = 100.0 if diff > 0 else (0.0 if diff == 0 else -100.0)

            # Determine status based on warning threshold
            if pct <= -warning_threshold_pct:
                status = "regressed"
                regressions += 1
            elif pct >= warning_threshold_pct:
                status = "improved"
                improvements += 1
            else:
                status = "unchanged"

            deltas[key] = MetricDelta(
                metric_name=key,
                baseline_value=b_val,
                current_value=c_val,
                delta=diff,
                delta_pct=pct,
                status=status,
            )

        summary = (
            f"Comparison completed: {improvements} improved, {regressions} regressed, "
            f"{len(deltas) - improvements - regressions} stable (threshold: {warning_threshold_pct}%)."
        )

        return RunComparisonResult(
            current_run_id=current_run.run_id,
            baseline_run_id=baseline_run.run_id,
            dataset_id=current_run.dataset_id,
            metric_deltas=deltas,
            regressions_count=regressions,
            improvements_count=improvements,
            has_regressions=regressions > 0,
            warning_threshold_pct=warning_threshold_pct,
            summary=summary,
        )
