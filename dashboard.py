"""Runtime dashboard for the Day 13 observability lab.

Run with: ``streamlit run dashboard.py``.
The dashboard intentionally reads the committed data contract's source,
``data/logs.jsonl``, rather than Langfuse. Langfuse remains the trace and
prompt-versioning tool for the lab.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st


REPO_ROOT = Path(__file__).resolve().parent
LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"
WINDOWS: dict[str, int | None] = {
    "15 minutes": 15,
    "60 minutes (default)": 60,
    "24 hours": 24 * 60,
    "All available data": None,
}


@st.cache_data(ttl=30, show_spinner=False)
def load_events(path: str, modified_ns: int) -> pd.DataFrame:
    """Load valid JSONL records and normalize their timestamps."""
    del modified_ns  # Cache invalidation key when the JSONL file changes.
    records: list[dict[str, Any]] = []
    log_path = Path(path)
    if not log_path.exists():
        return pd.DataFrame()

    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            records.append(event)

    if not records:
        return pd.DataFrame()

    frame = pd.DataFrame(records)
    if "ts" not in frame:
        return pd.DataFrame()
    frame["timestamp"] = pd.to_datetime(frame["ts"], utc=True, errors="coerce")
    return frame.dropna(subset=["timestamp"]).sort_values("timestamp")


def numeric(frame: pd.DataFrame, field: str) -> pd.Series:
    """Return a safe numeric field, including for incomplete log rows."""
    if field not in frame:
        return pd.Series(dtype="float64")
    return pd.to_numeric(frame[field], errors="coerce").dropna()


def records_for(frame: pd.DataFrame, event_name: str) -> pd.DataFrame:
    if frame.empty or "event" not in frame:
        return pd.DataFrame(columns=frame.columns)
    return frame[frame["event"] == event_name].copy()


def minute_buckets(frame: pd.DataFrame, field: str, aggregation: str) -> pd.DataFrame:
    """Aggregate one numeric field into one-minute buckets."""
    if frame.empty or field not in frame:
        return pd.DataFrame(columns=["minute", "value"])
    result = frame[["timestamp", field]].copy()
    result[field] = pd.to_numeric(result[field], errors="coerce")
    result = result.dropna(subset=[field])
    if result.empty:
        return pd.DataFrame(columns=["minute", "value"])
    result["minute"] = result["timestamp"].dt.floor("min")
    if aggregation == "p95":
        grouped = result.groupby("minute")[field].quantile(0.95)
    elif aggregation == "mean":
        grouped = result.groupby("minute")[field].mean()
    else:
        grouped = result.groupby("minute")[field].sum()
    return grouped.reset_index(name="value")


def threshold_chart(
    points: pd.DataFrame,
    *,
    title: str,
    unit: str,
    threshold: float,
    threshold_label: str,
) -> None:
    """Render an accessible time chart with an explicit SLO threshold line."""
    if points.empty:
        st.info("No data in the selected time range.")
        return

    base = (
        alt.Chart(points)
        .mark_line(point=True, color="#4c78a8")
        .encode(
            x=alt.X("minute:T", title="Time (UTC)"),
            y=alt.Y("value:Q", title=unit),
            tooltip=[
                alt.Tooltip("minute:T", title="Time"),
                alt.Tooltip("value:Q", title=title, format=".3f"),
            ],
        )
    )
    rule = (
        alt.Chart(pd.DataFrame({"value": [threshold]}))
        .mark_rule(color="#d62728", strokeDash=[6, 4])
        .encode(y="value:Q")
    )
    st.altair_chart((base + rule).properties(height=220), use_container_width=True)
    st.caption(f"Red dashed line: {threshold_label}")


def metric_or_dash(label: str, value: str) -> None:
    st.metric(label, value)


def render_dashboard(frame: pd.DataFrame) -> None:
    st.title("Day 13 AI Observability")
    st.caption("Runtime source: data/logs.jsonl · dashboard cache: 30 seconds")

    with st.sidebar:
        st.header("Dashboard controls")
        selected_window = st.selectbox("Time range", list(WINDOWS), index=1)
        st.caption("Configured refresh interval: 30 seconds")
        if st.button("Refresh data"):
            load_events.clear()
            st.rerun()

    if frame.empty:
        st.warning("No valid events found. Start the API and run the load test first.")
        return

    latest = frame["timestamp"].max()
    minutes = WINDOWS[selected_window]
    if minutes is not None:
        cutoff = latest - pd.Timedelta(minutes=minutes)
        frame = frame[frame["timestamp"] >= cutoff].copy()
    st.caption(
        f"Showing {len(frame)} events through {latest.strftime('%Y-%m-%d %H:%M:%S UTC')} "
        f"({selected_window})."
    )

    received = records_for(frame, "request_received")
    responses = records_for(frame, "response_sent")
    failures = records_for(frame, "request_failed")

    left, right = st.columns(2)
    with left:
        st.subheader("1. Latency percentiles")
        latency = numeric(responses, "latency_ms")
        c1, c2, c3 = st.columns(3)
        c1.metric("P50", f"{latency.quantile(0.50):.0f} ms" if not latency.empty else "—")
        c2.metric("P95", f"{latency.quantile(0.95):.0f} ms" if not latency.empty else "—")
        c3.metric("P99", f"{latency.quantile(0.99):.0f} ms" if not latency.empty else "—")
        threshold_chart(
            minute_buckets(responses, "latency_ms", "p95"),
            title="P95 latency",
            unit="Latency (ms)",
            threshold=3000,
            threshold_label="P95 latency ≤ 3,000 ms",
        )

    with right:
        st.subheader("2. Request traffic")
        traffic = received.copy()
        if not traffic.empty:
            traffic["minute"] = traffic["timestamp"].dt.floor("min")
            traffic_points = traffic.groupby("minute").size().reset_index(name="value")
        else:
            traffic_points = pd.DataFrame(columns=["minute", "value"])
        metric_or_dash("Requests in range", str(len(received)))
        threshold_chart(
            traffic_points,
            title="Requests",
            unit="Requests per minute",
            threshold=1,
            threshold_label="Traffic target ≥ 1 request/minute",
        )

    left, right = st.columns(2)
    with left:
        st.subheader("3. Error rate and breakdown")
        error_rate = (len(failures) / len(received) * 100) if len(received) else 0.0
        metric_or_dash("Error rate", f"{error_rate:.2f}%")
        st.caption("SLO: error rate ≤ 2.00%")
        if failures.empty:
            st.success("No request failures in the selected time range.")
        else:
            breakdown = failures.copy()
            if "error_type" not in breakdown:
                breakdown["error_type"] = "unknown"
            else:
                breakdown["error_type"] = breakdown["error_type"].fillna("unknown")
            st.bar_chart(breakdown["error_type"].value_counts())

    with right:
        st.subheader("4. Cost over time")
        costs = numeric(responses, "cost_usd")
        metric_or_dash("Total cost", f"${costs.sum():.4f}")
        threshold_chart(
            minute_buckets(responses, "cost_usd", "sum"),
            title="Cost",
            unit="USD per minute",
            threshold=2.5,
            threshold_label="Total-cost SLO ≤ $2.50 per window",
        )

    left, right = st.columns(2)
    with left:
        st.subheader("5. Input and output tokens")
        tokens_in = numeric(responses, "tokens_in")
        tokens_out = numeric(responses, "tokens_out")
        c1, c2 = st.columns(2)
        c1.metric("Input tokens", f"{tokens_in.sum():,.0f}")
        c2.metric("Output tokens", f"{tokens_out.sum():,.0f}")
        token_points = responses[["timestamp"]].copy()
        for token_field in ("tokens_in", "tokens_out"):
            if token_field in responses:
                token_points[token_field] = pd.to_numeric(
                    responses[token_field], errors="coerce"
                ).fillna(0)
            else:
                token_points[token_field] = 0
        if token_points.empty:
            st.info("No token data in the selected time range.")
        else:
            token_points["minute"] = token_points["timestamp"].dt.floor("min")
            token_points = token_points.groupby("minute")[["tokens_in", "tokens_out"]].sum()
            st.bar_chart(token_points)
            st.caption("SLO: combined token budget ≤ 50,000 tokens per window")

    with right:
        st.subheader("6. Quality proxy")
        quality = numeric(responses, "quality_score")
        metric_or_dash("Average quality", f"{quality.mean():.2f}" if not quality.empty else "—")
        threshold_chart(
            minute_buckets(responses, "quality_score", "mean"),
            title="Quality score",
            unit="Score (0–1)",
            threshold=0.75,
            threshold_label="Quality target ≥ 0.75",
        )


def main() -> None:
    st.set_page_config(page_title="Day 13 AI Observability", layout="wide")
    modified_ns = LOG_PATH.stat().st_mtime_ns if LOG_PATH.exists() else 0
    render_dashboard(load_events(str(LOG_PATH), modified_ns))


if __name__ == "__main__":
    main()
