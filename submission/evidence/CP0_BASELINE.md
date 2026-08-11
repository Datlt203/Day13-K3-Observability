# CP0 — setup and baseline

Initial inspection on 2026-08-11 found that CP0 was not complete.

- `data/logs.jsonl` did not exist; `python scripts/validate_logs.py` returned: `Error: data\\logs.jsonl not found. Run the app and send some requests first.`
- The application was started locally and `/health` returned HTTP 200 with `ok: true` and `tracing_enabled: false`.
- `python scripts/validate_dashboard.py` already passed the dashboard contract: `HỢP LỆ: 6/6 panel có trong dashboard contract.`

The missing log baseline was addressed by completing CP1, then exercising the API with the 10 supplied queries and one PII test request. The resulting verification is recorded in CP1 evidence.
