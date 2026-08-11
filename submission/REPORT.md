# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:
  - **[PHẦN CỦA TÔI — THÀNH VIÊN A] Nguyễn Hữu Nhật Minh — MSSV: 2A202601551** — API & Middleware: CP1 Middleware, Correlation ID và exception handler.

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 30/100 (Baseline CP0)
  ```text
  --- Lab Verification Results ---
  Total log records analyzed: 22
  Records with missing required fields: 20
  Records with missing enrichment (context): 20
  Unique correlation IDs found: 0
  Potential PII leaks detected: 0

  --- Grading Scorecard (Estimates) ---
  - [FAILED] Missing required fields (ts, level, etc.)
  - [FAILED] Correlation ID propagation (less than 2 unique IDs)
  - [FAILED] Log enrichment (missing user_id_hash, etc.)
  + [PASSED] PII scrubbing

  Estimated Score: 30/100
  ```
- Tổng số traces:
- Số PII leak còn lại:
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- **[PHẦN CỦA TÔI — THÀNH VIÊN A] Evidence correlation ID:**
  - Middleware xóa context cũ ở đầu mỗi request, nhận `x-request-id` hợp lệ từ client hoặc sinh ID theo mẫu `req-<8 ký tự hex>`.
  - Correlation ID được bind vào structlog, lưu trong `request.state` và trả lại qua response header `x-request-id`.
  - Response có thêm `x-response-time-ms`; các event `request_received`, `response_sent` và `request_failed` của cùng request dùng chung correlation ID.
  - Đường dẫn evidence: `submission/evidence/TODO-correlation-id.png`
- **[PHẦN CỦA TÔI — THÀNH VIÊN A] Evidence exception handler:**
  - Lỗi trong `/chat` được ghi bằng event `request_failed`, có `error_type` và correlation ID.
  - Exception chưa được endpoint xử lý được global handler chuyển thành JSON 500 an toàn, không trả stack trace hoặc chi tiết lỗi nội bộ cho client.
  - Response lỗi vẫn có `x-request-id` và `x-response-time-ms`.
  - Kết quả kiểm thử: `28 passed`.
  - Đường dẫn evidence: `submission/evidence/TODO-exception-handler.png`
- Evidence PII redaction:
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`:
- Evidence dashboard:
- SLO đã chọn và lý do:
- Alert rules và runbook:

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| **Nguyễn Hữu Nhật Minh — 2A202601551 (Thành viên A)** | Hoàn thiện middleware; sinh/propagate Correlation ID; bind log context; thêm response timing; bổ sung xử lý lỗi `/chat` và global exception handler; viết test API/middleware | `TODO: commit SHA/PR của A` | Correlation ID phải xuyên suốt request, response và structured log; exception response cần an toàn nhưng vẫn giữ đủ metadata để điều tra sự cố. |
| | | | |
