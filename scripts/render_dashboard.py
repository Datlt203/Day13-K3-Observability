"""Render a portable six-panel dashboard snapshot from structured JSON logs."""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean


def percentile(values: list[float], point: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((point / 100) * len(ordered) + 0.5) - 1))
    return ordered[index]


def load_records(path: Path) -> list[dict]:
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def format_number(value: float, digits: int = 2) -> str:
    return f"{value:,.{digits}f}"


def dashboard_html(records: list[dict]) -> str:
    received = [record for record in records if record.get("event") == "request_received"]
    responses = [record for record in records if record.get("event") == "response_sent"]
    failures = [record for record in records if record.get("event") == "request_failed"]
    latencies = [float(record["latency_ms"]) for record in responses if isinstance(record.get("latency_ms"), (int, float))]
    costs = [float(record["cost_usd"]) for record in responses if isinstance(record.get("cost_usd"), (int, float))]
    tokens_in = sum(int(record.get("tokens_in", 0)) for record in responses)
    tokens_out = sum(int(record.get("tokens_out", 0)) for record in responses)
    quality = [float(record["quality_score"]) for record in responses if isinstance(record.get("quality_score"), (int, float))]
    error_rate = (len(failures) / len(received) * 100) if received else 0.0
    errors = Counter(str(record.get("error_type", "unknown")) for record in failures)
    timestamps = [str(record["ts"]) for record in records if record.get("ts")]
    timerange = f"{min(timestamps)} to {max(timestamps)}" if timestamps else "No valid log events"
    panels = [
        ("Latency", f"P50 {format_number(percentile(latencies, 50), 0)} ms · P95 {format_number(percentile(latencies, 95), 0)} ms · P99 {format_number(percentile(latencies, 99), 0)} ms", "P95 SLO ≤ 3,000 ms"),
        ("Traffic", f"{len(received)} requests · {len(responses)} completed", "Source: request_received"),
        ("Errors", f"{format_number(error_rate)}% error rate · {dict(errors) or 'no failures'}", "SLO ≤ 2%"),
        ("Cost", f"USD {format_number(sum(costs), 4)} total", "Daily budget ≤ USD 2.50"),
        ("Tokens", f"{tokens_in:,} input · {tokens_out:,} output", "Window guideline ≤ 50,000"),
        ("Quality", f"{format_number(mean(quality) if quality else 0.0)} / 1.00", "SLO ≥ 0.75"),
    ]
    panel_html = "".join(
        "<section class='panel'><h2>{}</h2><p class='value'>{}</p><p class='threshold'>{}</p></section>".format(
            html.escape(title), html.escape(value), html.escape(threshold)
        )
        for title, value, threshold in panels
    )
    return f"""<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><title>Day 13 dashboard snapshot</title>
<style>
body {{ font-family: Arial, sans-serif; color: #172033; margin: 36px; background: #f7f9fc; }}
h1 {{ margin-bottom: 6px; }} .meta {{ color: #53627a; margin-top: 0; }}
.grid {{ display: grid; grid-template-columns: repeat(3, minmax(220px, 1fr)); gap: 16px; margin-top: 28px; }}
.panel {{ background: #fff; border: 1px solid #cdd7e5; border-radius: 10px; padding: 18px; min-height: 118px; }}
h2 {{ font-size: 18px; margin: 0 0 18px; }} .value {{ font-size: 20px; font-weight: 600; margin: 0 0 14px; }}
.threshold {{ color: #53627a; margin: 0; }}
@media (max-width: 760px) {{ body {{ margin: 20px; }} .grid {{ grid-template-columns: 1fr; }} }}
</style></head><body>
<h1>Day 13 AI Observability</h1>
<p class=\"meta\">Six-panel runtime snapshot · configured range: 60 minutes · refresh target: 30 seconds</p>
<p class=\"meta\">Log window: {html.escape(timerange)}</p>
<main class=\"grid\">{panel_html}</main>
</body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs", type=Path, default=Path("data/logs.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("submission/evidence/dashboard-runtime.html"))
    args = parser.parse_args()
    if not args.logs.exists():
        raise SystemExit(f"Không tìm thấy log source: {args.logs}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(dashboard_html(load_records(args.logs)), encoding="utf-8")
    print(f"Dashboard snapshot written to {args.output}")


if __name__ == "__main__":
    main()
