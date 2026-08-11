from app import metrics
from app.metrics import percentile


def test_percentile_basic() -> None:
    assert percentile([100, 200, 300, 400], 50) >= 100


def test_error_rate_uses_received_requests_as_denominator(monkeypatch) -> None:
    monkeypatch.setattr(metrics, "TRAFFIC", 0)
    monkeypatch.setattr(metrics, "ERRORS", metrics.Counter())

    metrics.record_received()
    metrics.record_received()
    metrics.record_error("RuntimeError")

    snapshot = metrics.snapshot()

    assert snapshot["traffic"] == 2
    assert snapshot["error_count"] == 1
    assert snapshot["error_rate_pct"] == 50.0
