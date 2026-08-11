# CP1 — logging, correlation ID, and PII

## Verification result

After a 10-query baseline load test plus one request containing email, phone, test-card, and address data types, `python scripts/validate_logs.py` reported:

```text
Total log records analyzed: 49
Records with missing required fields: 0
Records with missing enrichment (context): 0
Unique correlation IDs found: 12
Potential PII leaks detected: 0
Estimated Score: 100/100
```

## Correlation evidence

The PII test sent `x-request-id: req-deadbeef`. The API returned the same value in response-body `correlation_id` and response-header `x-request-id`; it also returned `x-response-time-ms`. Invalid/missing inbound IDs are replaced by the validated `req-<8 lowercase hex>` format.

## Sanitization evidence

The matching `request_received` log for `req-deadbeef` contains only `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, and a truncated `[REDACTED_CREDIT…]` preview. The validator independently detected zero raw PII leaks. The scrubber applies recursively to every string in the final structured event, including nested payloads and exception text.
