# Alert rules and runbook

All alerts describe an observable user or budget symptom. They deliberately do
not alert on a private implementation flag such as `rag_slow`; that flag is a
possible diagnosis, not a user-facing symptom.

## Alert 1 — chat-error-rate-slo-breach

- Severity: **critical**.
- SLI/SLO: `error_rate_pct <= 2%`; fires when the rate is above 2% for 5 minutes and at least 20 requests were received.
- User impact: chat requests are failing and may return HTTP 500.
- First checks:
  1. Confirm traffic and `request_failed` counts in the Errors panel; record the affected time window.
  2. Open one failed local/Langfuse trace in that window and identify the first failed span.
  3. Filter `data/logs.jsonl` by its `correlation_id`, then compare `error_type` and `tool_name` with the trace.
- Temporary mitigation: disable the affected feature/incident path if safe, or route requests to the general fallback response while the dependency recovers.
- Resolution: verify five clean minutes at normal traffic, then close the alert with trace ID and correlation ID in the incident note.
- Owner: Thành viên D; Thành viên A supports API recovery and Thành viên E validates the fix.

## Alert 2 — chat-latency-p95-slo-breach

- Severity: **warning**; escalate to critical if P95 exceeds 6,000 ms for 10 minutes.
- SLI/SLO: `latency_p95_ms <= 3,000`; fires above 3,000 ms for 10 minutes with at least 10 completed requests.
- User impact: users experience a slow answer even if requests ultimately succeed.
- First checks:
  1. Compare latency P50/P95/P99 to determine whether the issue is broad or a tail-latency problem.
  2. Open the slowest trace and compare `rag_retrieve` and `llm_generate` span durations.
  3. Filter component logs by the matching `trace_id`/`correlation_id` and check `tool_name`, `latency_ms`, and recent incident controls.
- Temporary mitigation: bypass slow retrieval for a short safe window, reduce concurrency, or serve the general fallback answer.
- Resolution: disable the mitigation after P95 is below 3,000 ms for two windows; attach before/after metrics and one trace waterfall.
- Owner: Thành viên D; Thành viên E leads the technical investigation.

## Alert 3 — daily-cost-budget-burn

- Severity: **warning**.
- SLI/SLO: `daily_cost_usd <= 2.50`; fires once the cumulative UTC-day cost is above USD 2.50.
- User impact: no immediate outage, but continued traffic could exhaust the budget or force a service restriction.
- First checks:
  1. Confirm total cost and output-token trend in the Cost and Tokens panels.
  2. Open representative high-cost traces and compare `llm_generate` token usage and prompt version.
  3. Filter logs for `cost_usd` and check whether a traffic rise, output-token spike, or a prompt-label change explains the increase.
- Temporary mitigation: cap output length, route to the approved lower-cost model, or roll back the latest prompt label.
- Resolution: document the chosen mitigation, cost before/after, and owner approval before restoring the normal configuration.
- Owner: Thành viên D; Thành viên C verifies dashboard calculations and Thành viên E validates the rollback.
