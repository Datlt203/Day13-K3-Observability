from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_slos_have_comparators_and_documented_targets() -> None:
    payload = yaml.safe_load((REPO_ROOT / "config" / "slo.yaml").read_text(encoding="utf-8"))

    assert payload["window"] == "28d"
    assert set(payload["slis"]) == {
        "latency_p95_ms",
        "error_rate_pct",
        "daily_cost_usd",
        "quality_score_avg",
    }
    for sli in payload["slis"].values():
        assert sli["comparator"] in {"lte", "gte"}
        assert isinstance(sli["objective"], (int, float))
        assert sli["note"]


def test_alert_rules_have_real_conditions_and_runbooks() -> None:
    payload = yaml.safe_load(
        (REPO_ROOT / "config" / "alert_rules.yaml").read_text(encoding="utf-8")
    )

    alerts = payload["alerts"]
    assert [alert["name"] for alert in alerts] == [
        "chat-error-rate-slo-breach",
        "chat-latency-p95-slo-breach",
        "daily-cost-budget-burn",
    ]
    assert all(alert["severity"] in {"warning", "critical"} for alert in alerts)
    assert all("TODO" not in str(alert) for alert in alerts)

    runbook = (REPO_ROOT / "docs" / "alerts.md").read_text(encoding="utf-8")
    for alert in alerts:
        assert alert["name"].replace("-", " ") in runbook.lower()
