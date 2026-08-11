"""Metrics collection module for tracking AI request performance, costs, and quality."""
from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Dict, List, Any

# Global metrics storage
REQUEST_LATENCIES: List[int] = []
REQUEST_COSTS: List[float] = []
REQUEST_TOKENS_IN: List[int] = []
REQUEST_TOKENS_OUT: List[int] = []
ERRORS: Counter[str] = Counter()
TRAFFIC: int = 0
QUALITY_SCORES: List[float] = []


def record_received() -> None:
    """Counts every accepted chat request, including requests that later fail."""
    global TRAFFIC
    TRAFFIC += 1


def record_request(latency_ms: int, cost_usd: float, tokens_in: int, tokens_out: int, quality_score: float) -> None:
    """Records metrics for a single request."""
    REQUEST_LATENCIES.append(latency_ms)
    REQUEST_COSTS.append(cost_usd)
    REQUEST_TOKENS_IN.append(tokens_in)
    REQUEST_TOKENS_OUT.append(tokens_out)
    QUALITY_SCORES.append(quality_score)


def record_error(error_type: str) -> None:
    """Increments the error count for a specific error type."""
    ERRORS[error_type] += 1


def percentile(values: List[int], p: int) -> float:
    """Calculates the p-th percentile of the given list of values."""
    if not values:
        return 0.0
    items = sorted(values)
    idx = max(0, min(len(items) - 1, round((p / 100) * len(items) + 0.5) - 1))
    return float(items[idx])


def snapshot() -> Dict[str, Any]:
    """Generates a snapshot of current system metrics."""
    error_count = sum(ERRORS.values())
    return {
        "traffic": TRAFFIC,
        "latency_p50": percentile(REQUEST_LATENCIES, 50),
        "latency_p95": percentile(REQUEST_LATENCIES, 95),
        "latency_p99": percentile(REQUEST_LATENCIES, 99),
        "avg_cost_usd": round(mean(REQUEST_COSTS), 4) if REQUEST_COSTS else 0.0,
        "total_cost_usd": round(sum(REQUEST_COSTS), 4),
        "tokens_in_total": sum(REQUEST_TOKENS_IN),
        "tokens_out_total": sum(REQUEST_TOKENS_OUT),
        "error_count": error_count,
        "error_rate_pct": round((error_count / TRAFFIC) * 100, 2) if TRAFFIC else 0.0,
        "error_breakdown": dict(ERRORS),
        "quality_avg": round(mean(QUALITY_SCORES), 4) if QUALITY_SCORES else 0.0,
    }
