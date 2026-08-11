# Dashboard specification

The primary dashboard has exactly six decision panels. Its source of truth is
`data/logs.jsonl`; `/metrics` is a convenient live summary using the same
definitions. Default time range is 60 minutes and refresh is 30 seconds.

| Panel | Calculation | Unit and SLO line | Decision supported |
|---|---|---|---|
| Latency | P50, P95, P99 of `response_sent.latency_ms` | ms; P95 <= 3,000 | Is slowness broad or limited to the tail? |
| Traffic | Count of `request_received` and requests/minute | requests/minute; >= 1 expected during demo | Is there enough traffic to trust a percentage? |
| Errors | `request_failed / request_received * 100`, grouped by `error_type` | percent; <= 2% | Are users failing and which error dominates? |
| Cost | Sum of `response_sent.cost_usd` by minute and over the window | USD; <= 2.50/day | Is spend rising faster than planned? |
| Tokens | Sum `tokens_in` and `tokens_out` from `response_sent` | tokens; <= 50,000/window | Does token growth explain cost or latency? |
| Quality | Mean `response_sent.quality_score` | score 0–1; >= 0.75 | Did a change degrade the response proxy? |

The checked contract is [config/dashboard.yaml](../config/dashboard.yaml). The
`errors` panel uses received requests as its denominator, so a failed request is
not accidentally omitted from `error_rate_pct`.

## Investigation hand-off

1. Start at an affected metric and record its time window.
2. Find a trace with a matching `correlation_id`; the local journal stores
   `rag_retrieve` and `llm_generate` span durations when Langfuse is unavailable.
3. Filter structured logs by `trace_id` or `correlation_id` to prove the root cause.
4. Link the three artifacts in the incident report before proposing a fix.
