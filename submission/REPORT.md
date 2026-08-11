# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: Day13-K3-Observability
- Repository URL: https://github.com/Datlt203/Day13-K3-Observability
- Thành viên A: Nguyễn Hữu Nhật Minh — MSSV: 2A202601551 — API & Middleware.
- Thành viên B: Bùi Văn Khởi — MHV: 2A202601723 — Security Engineer: CP1 PII Scrubbing, regex patterns và kiểm chứng log.
- Thành viên C: Lê Văn Huy — MSSV: 2A202601235 — Metrics & Dashboard: CP1/CP2 đo đếm error_rate_pct và thiết kế spec Dashboard 6 nhóm chỉ số.

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

- `submission/evidence/pii-redaction-test.txt`: kết quả test.
- `submission/evidence/validate-logs.txt`: kết quả `python scripts/validate_logs.py`.
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

## 6. Kiểm thử

- Chạy: `python -m pytest -q`
- Chạy validator sau khi tạo log: `python scripts/validate_logs.py`
- Tiêu chí đạt CP1: không còn email, phone, CCCD hoặc credit card nguyên văn trong log; validator không báo PII leak.

## 7. Đóng góp cá nhân

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Nguyễn Hữu Nhật Minh — 2A202601551 (A) | Middleware, correlation ID, timing và exception handler | TODO | Correlation ID phải xuyên suốt request, response và log. |
| Bùi Văn Khởi — 2A202601723 (B) | Thiết kế regex PII; triển khai scrub đệ quy toàn event; đăng ký processor trước JSON renderer/file writer; bổ sung test kiểm chứng log không lộ PII. | TODO: commit SHA/PR của B | Redaction phải xảy ra trước khi render/ghi log; cần kiểm tra độc lập trên JSONL thay vì chỉ tin processor. |
| Lê Văn Huy — 2A202601235 (C) | Triển khai metric `error_rate_pct`, thiết kế Dashboard spec với 6 nhóm chỉ số giám sát. | Implemented (Verified) | Cách xây dựng metric từ log thô, tầm quan trọng của việc chọn đúng denominator (request_received) khi tính error rate. |