# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: Day13-K3-Observability
- Repository URL: https://github.com/Datlt203/Day13-K3-Observability
- Thành viên A: Nguyễn Hữu Nhật Minh — MSSV: 2A202601551 — API & Middleware.
- Thành viên B: Bùi Văn Khởi — MHV: 2A202601723 — Security Engineer: CP1 PII Scrubbing, regex patterns và kiểm chứng log.
- Thành viên C: Lê Văn Huy — MSSV: 2A202601235 — Metrics & Dashboard: CP1/CP2 đo đếm error_rate_pct và thiết kế spec Dashboard 6 nhóm chỉ số.
- Thành viên D: Lý Thành Đạt — 2A202601469 SRE & Alerts Engineer — CP2 thiết lập SLO, alert rules và alert runbook xử lý sự cố.
- Thành viên E: Ngô Hữu Nghĩa — 2A202601924 QA & Chief Investigator — load test, trace RAG/LLM, điều tra Challenge CP3 và tổng hợp evidence.

## 2. Kết quả kỹ thuật

- CP1 tập trung bảo vệ log khỏi email, số điện thoại Việt Nam, CCCD 12 chữ số và số thẻ thử nghiệm.
- Bộ nhận diện dùng regex có tên rõ ràng trong `app/pii.py`; các pattern được compile một lần để tái sử dụng.
- `scrub_event` được đăng ký trong pipeline structlog trước `JsonlFileProcessor`, bảo đảm dữ liệu đã redact trước khi render và ghi xuống `data/logs.jsonl`.
- Validator độc lập `scripts/validate_logs.py` được dùng để tìm lại PII nguyên văn trong JSON log.

## 3. Phần việc của thành viên B

### 3.1. PII scrubbing

`app/pii.py` cung cấp `scrub_text()` với các pattern:

| Loại dữ liệu | Pattern/kiểm chứng |
|---|---|
| Email | local-part và domain nhiều nhãn |
| Điện thoại VN | `0xxxxxxxxx`, dạng cách/chấm/gạch và `+84` |
| CCCD | đúng 12 chữ số |
| Credit card | 16 chữ số, có thể ngăn cách bằng khoảng trắng/gạch |

Giá trị bị thay bằng token có dạng `[REDACTED_<TYPE>]`. Scrubbing được áp dụng đệ quy cho string, dict, list và tuple trong toàn bộ event, gồm cả context fields và payload lồng nhau.

### 3.2. Kiểm chứng

Đã bổ sung test `test_chat_log_scrubs_pii_from_nested_payload_and_context` trong `tests/test_chat_observability.py`. Test gửi email và số điện thoại qua `/chat`, đọc JSONL thực tế, xác nhận dữ liệu nguyên văn không xuất hiện và token redaction xuất hiện.

Evidence đề xuất khi chạy demo:

- [pii-redaction-log.txt](evidence/pii-redaction-log.txt): log đã được redact.
- [validate-logs.txt](evidence/validate-logs.txt): kết quả `python scripts/validate_logs.py`.
- `data/logs.jsonl`: log JSONL sau khi scrub, không commit dữ liệu thật hoặc secret.

## 4. Logging và tracing của nhóm

- Middleware của thành viên A sinh/propagate correlation ID, bind vào log context và trả về header `x-request-id`.
- Các event API giữ `user_id_hash`, `session_id`, `feature`, `model`, `env`; không ghi raw `user_id`.
- Log request/response dùng preview đã được scrub, còn lỗi trả về client không chứa chi tiết nội bộ.

## 5. Phần việc của thành viên C (Metrics & Dashboard)

### 5.1. Thiết lập Metrics
`app/metrics.py` triển khai các cơ chế:
- Đo đếm `error_rate_pct` chính xác bằng cách dùng `request_received` làm mẫu số.
- Tính toán latency percentiles (P50, P95, P99), tổng chi phí và token usage.

### 5.2. Thiết kế Dashboard
`config/dashboard.yaml` định nghĩa 6 panel giám sát toàn diện:
1. Latency (P50, P95, P99)
2. Traffic (requests/minute)
3. Errors (error rate & breakdown)
4. Cost (USD/time)
5. Tokens (in/out)
6. Quality (score)

Các chỉ số được kiểm chứng thông qua `docs/dashboard-spec.md`.

Dashboard runtime đọc trực tiếp `data/logs.jsonl` được chạy từ
[dashboard.py](../dashboard.py); ảnh runtime có đủ sáu panel tại
[dashboard-six-panels.png](evidence/dashboard-six-panels.png).

## 6. Kiểm thử

- Chạy: `python -m pytest -q`
- Chạy validator sau khi tạo log: `python scripts/validate_logs.py`
- Tiêu chí đạt CP1: không còn email, phone, CCCD hoặc credit card nguyên văn trong log; validator không báo PII leak.

### 6.1. Evidence nộp kèm

- [pytest.txt](evidence/pytest.txt), [validate-logs.txt](evidence/validate-logs.txt) và [validate-dashboard.txt](evidence/validate-dashboard.txt) là kết quả kiểm tra tự động.
- [traces-list.png](evidence/traces-list.png) chứng minh có tối thiểu 10 root traces.
- [prompt-versions.png](evidence/prompt-versions.png) chứng minh prompt `day13-chat` có version 1 và 2.
- Trace baseline: ID `256831ec09f5d48263015855f4145e6b`, metadata `prompt_label=baseline`, `prompt_version=1`, `prompt_source=langfuse`; xem [prompt-baseline-trace.png](evidence/prompt-baseline-trace.png).
- Trace candidate: ID `7f6b967801101a1f9b215d8a5393bcd3`, metadata `prompt_label=candidate`, `prompt_version=2`, `prompt_source=langfuse`; xem [prompt-candidate-trace.png](evidence/prompt-candidate-trace.png).
- [prompt-production-v2.png](evidence/prompt-production-v2.png) chứng minh đã chuyển label `production` sang version 2; [prompt-production-rollback-v1.png](evidence/prompt-production-rollback-v1.png) chứng minh rollback `production` về version 1.
- [dashboard-six-panels.png](evidence/dashboard-six-panels.png) hiển thị latency, traffic, errors, cost, tokens và quality kèm time range/threshold.

## 7. Phần việc của thành viên D (SRE & Alerts Engineer)

- [config/slo.yaml](../config/slo.yaml) xác định SLO cho P95 latency, error rate, daily cost và quality proxy trong cửa sổ 28 ngày.
- [config/alert_rules.yaml](../config/alert_rules.yaml) có ba alert symptom-based: error-rate breach, latency P95 breach và daily-cost budget burn.
- [docs/alerts.md](../docs/alerts.md) là runbook Metrics → Traces → Logs, gồm ba bước kiểm tra đầu tiên, mitigation, điều kiện resolve và owner.

## 8. Điều tra Challenge CP3

- Challenge: `day13-k3-observability-v1`; incident chính thức: `rag_slow`; feature bị ảnh hưởng: `refund`.
- Triệu chứng metric: P95 latency tăng từ **408 ms** (baseline 10 request) lên **2,685 ms** (challenge 15 request), trong khi `error_rate_pct` vẫn 0.00%.
- Trace Langfuse evidence: ID `12dc7f0963aa5928861c32b65279fbb3`, correlation ID `req-cp3-rag-slow-001`; waterfall có `rag_retrieve` và `llm_generate` tại [cp3-rag-slow-trace.png](evidence/cp3-rag-slow-trace.png).
- Log chứng minh cùng correlation ID: `rag_retrieve` mất **2,500 ms** tại `2026-08-11T08:18:30.904510Z`; `llm_generate` chỉ **151 ms**; API response mất **5,483 ms**. Xem [cp3-correlation-log.txt](evidence/cp3-correlation-log.txt) và [cp3-metrics.json](evidence/cp3-metrics.json).
- Root cause: `rag_slow` thêm delay 2.5 giây trong `app/mock_rag.py`. Fix lab đã thực hiện: disable incident. Phòng ngừa production: timeout retrieval, fallback an toàn và điều tra theo Metrics → Traces → Logs.
- Tái lập: chạy baseline bằng `python scripts/load_test.py --concurrency 5`; bật incident `rag_slow`; chạy `python scripts/load_test.py --challenge --concurrency 5`; sau khi thu evidence thì tắt incident.
- Evidence CP3 đã lưu trong các file liên kết ở trên; trace ID và correlation ID là giá trị thật từ lần chạy evidence.

## 9. Đóng góp cá nhân

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Nguyễn Hữu Nhật Minh — 2A202601551 (A) | Middleware, correlation ID, timing và exception handler | TODO | Correlation ID phải xuyên suốt request, response và log. |
| Bùi Văn Khởi — 2A202601723 (B) | Thiết kế regex PII; triển khai scrub đệ quy toàn event; đăng ký processor trước JSON renderer/file writer; bổ sung test kiểm chứng log không lộ PII. | TODO: commit SHA/PR của B | Redaction phải xảy ra trước khi render/ghi log; cần kiểm tra độc lập trên JSONL thay vì chỉ tin processor. |
| Lê Văn Huy — 2A202601235 (C) | Triển khai metric `error_rate_pct`, thiết kế Dashboard spec với 6 nhóm chỉ số giám sát. | Implemented (Verified) | Cách xây dựng metric từ log thô, tầm quan trọng của việc chọn đúng denominator (request_received) khi tính error rate. |
| Lý Thành Đạt — 2A202601469 SRE & Alerts Engineer | Chốt 4 SLO, 3 alert symptom-based và runbook xử lý sự cố. | Pending commit | Alert cần dựa trên ảnh hưởng/SLO; trace và log chỉ được dùng để khoanh vùng nguyên nhân. |
| Ngô Hữu Nghĩa — 2A202601924 QA & Chief Investigator | Bọc trace `rag_retrieve`/`llm_generate`, chạy challenge và nối Metrics → Traces → Logs. | Pending challenge evidence | Trace cho biết span bất thường; correlation ID nối trace với log để chứng minh root cause. |
