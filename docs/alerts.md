# Alert rules and incident runbook

Each alert is based on a user-visible symptom or an approved SLO. An internal
implementation flag is evidence for diagnosis, never the alert condition.

## Alert 1: Chat error rate SLO breach

- Severity: **critical**.
- SLI/SLO: `error_rate_pct <= 2%`; fires above 2% for 5 minutes with at least 20 received requests.
- User impact: chat requests are failing and may return HTTP 500.
- First checks:
  1. Confirm `request_received`, `request_failed`, `error_rate_pct`, and the `error_type` breakdown in the Errors panel.
  2. Open a failed trace in the affected window; identify the first failed observation/span.
  3. Filter `data/logs.jsonl` by its `correlation_id`; compare `error_type` and `tool_name` with the trace.
- Temporary mitigation: disable the affected feature path when safe, or serve the approved general fallback answer while the dependency recovers.
- Resolution: verify five clean minutes at normal traffic, then close the incident with its metric window, trace ID, and correlation ID.
- Owner: Thành viên D. Thành viên A supports API recovery; Thành viên E validates the mitigation.

## Alert 2: Chat latency P95 SLO breach

- Severity: **warning**; escalate to critical if P95 exceeds 6,000 ms for 10 minutes.
- SLI/SLO: `latency_p95_ms <= 3,000`; fires above 3,000 ms for 10 minutes with at least 10 completed requests.
- User impact: users receive answers slowly even when requests eventually succeed.
- First checks:
  1. Compare latency P50/P95/P99 to determine whether the issue is broad or tail latency.
  2. Open the slowest trace and compare `rag_retrieve` and `llm_generate` observation durations.
  3. Filter structured logs with the matching `correlation_id`, then inspect `tool_name`, `latency_ms`, and recent incident-control events.
- Temporary mitigation: bypass slow retrieval for a short safe window, reduce concurrency, or serve the general fallback answer.
- Resolution: remove mitigation only after P95 is below 3,000 ms for two windows; attach before/after metrics and one trace waterfall.
- Owner: Thành viên D. Thành viên E leads root-cause investigation.

## Alert 3: Daily cost budget burn

- Severity: **warning**.
- SLI/SLO: `daily_cost_usd <= 2.50`; fires once UTC-day cumulative cost exceeds USD 2.50.
- User impact: continued traffic can exhaust budget and force service restrictions.
- First checks:
  1. Confirm total cost and output-token trend in Cost and Tokens panels.
  2. Open representative high-cost traces and compare `llm_generate` token usage and prompt version.
  3. Filter `response_sent` logs by high `cost_usd`; check whether traffic, output-token growth, or a prompt-label change explains it.
- Temporary mitigation: cap output length, route to an approved lower-cost model, or roll back the latest prompt label.
- Resolution: record the cost before/after mitigation and obtain owner approval before restoring the normal configuration.
- Owner: Thành viên D. Thành viên C verifies dashboard calculations; Thành viên E validates a prompt rollback.
