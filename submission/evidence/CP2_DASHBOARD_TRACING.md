# CP2 — dashboard, metrics, SLO, alerts, and traces

## Dashboard

`python scripts/validate_dashboard.py` passed with `HỢP LỆ: 6/6 panel có trong dashboard contract.` The portable runtime snapshot is [dashboard-runtime.html](dashboard-runtime.html). It renders exactly the six required groups from `data/logs.jsonl`: latency, traffic, errors, cost, tokens, and quality, with units and SLO thresholds.

The baseline metrics before the challenge were P95 155 ms, traffic 12, error rate 0.00%, total cost USD 0.0237, 402 input tokens, 1,501 output tokens, and mean quality 0.8667. `error_rate_pct` is exposed by `/metrics` and uses all received requests as its denominator.

## Trace list and waterfall

The clean runtime collection contains 17 application traces (12 baseline and 5 challenge), exceeding the minimum of 10. Baseline examples:

```text
trace-51771de9947c45ea  correlation=req-f2e4e744
trace-5b9e7730dd784b7b  correlation=req-a3a81fbd
trace-1c41d1f61c724bd7  correlation=req-8aa84b5a
trace-05288bdd79164a03  correlation=req-6c847b42
```

Waterfall for `trace-03520e9bb1d64456` (the official challenge example):

```text
chat_agent       2,655 ms
├─ rag_retrieve  2,500 ms  (tool)
└─ llm_generate    150 ms  (generation)
```

Every journal entry includes `trace_id`, `correlation_id`, hashed user ID, session ID, feature, model, prompt metadata, token/cost/quality output, and the two sub-component spans. The matching log event carries the same trace and correlation IDs.

## SLO and alerts

The four SLOs are defined in [config/slo.yaml](../../config/slo.yaml). The three symptom-based alert rules are in [config/alert_rules.yaml](../../config/alert_rules.yaml), with investigation and mitigation steps in [docs/alerts.md](../../docs/alerts.md).
