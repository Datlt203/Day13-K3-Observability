# CP3 — official challenge investigation

## Reproduction

The released `config/challenge.json` was used without modification:

```text
Challenge: day13-k3-observability-v1 | Cohort: K3
Incident: rag_slow
```

After enabling the released incident and running `python scripts/load_test.py --challenge --concurrency 5`, API metrics changed from P95 **155 ms** (baseline) to P95 **2,658 ms**. Traffic reached 17 requests and `error_rate_pct` remained 0.00%, so this is a latency symptom rather than a failure symptom.

## Metrics → traces → logs

- **Metric:** `/metrics` reported `latency_p95: 2658.0` and `latency_p99: 2658.0`.
- **Trace:** `trace-03520e9bb1d64456` has correlation ID `req-49d31ab8`; its `rag_retrieve` span took 2,500 ms, whereas `llm_generate` took 150 ms.
- **Log:** the `component_completed` event at `2026-08-11T03:13:52.047491Z` has `tool_name: rag_retrieve`, `latency_ms: 2500`, the same trace ID/correlation ID, and `feature: refund`. The final API `response_sent` for that request took 2,655 ms.

## Root cause and response

The official `rag_slow` incident makes the retrieval dependency sleep for 2.5 seconds in `app/mock_rag.py`. It dominates end-to-end latency; the LLM does not.

- **Fix action:** disable the incident/degraded retrieval path (completed after evidence collection), then restore normal retrieval latency.
- **Preventive measure:** keep the P95 latency alert, use the trace comparison to detect retrieval dominance, and add a bounded retrieval timeout with a safe general-answer fallback before a future production rollout.
