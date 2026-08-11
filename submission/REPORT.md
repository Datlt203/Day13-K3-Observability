# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: Day13-K3-Observability.
- Repository URL: https://github.com/Datlt203/Day13-K3-Observability
- Commit SHA cuối: chưa tạo trong sandbox; working tree đã sẵn sàng và cần quyền tạo commit trên nhánh `main`.
- Thành viên và vai trò: A — API & Middleware; B — Security Engineer; C — Metrics & Dashboard; D — SRE & Alerts Engineer; E — QA & Chief Investigator.

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: **100/100** (75 log record cuối; 0 trường bắt buộc/enrichment thiếu; 19 correlation ID; 0 PII leak).
- Tổng số trace ứng dụng của lượt chạy evidence: **17** (12 baseline + 5 challenge); xem [CP2 evidence](evidence/CP2_DASHBOARD_TRACING.md).
- Số PII leak còn lại: **0**.
- Dashboard runtime: [dashboard-runtime.html](evidence/dashboard-runtime.html); dashboard contract: [config/dashboard.yaml](../config/dashboard.yaml).

## 3. Logging và tracing

- Evidence correlation ID: [CP1 logging/PII](evidence/CP1_LOGGING_PII.md). `req-deadbeef` được truyền nguyên vẹn từ request header sang body/header response.
- Evidence PII redaction: cùng tài liệu CP1; email, điện thoại, số thẻ và địa chỉ chỉ có token `[REDACTED_*]` trong log.
- Evidence trace waterfall: [CP2 dashboard/tracing](evidence/CP2_DASHBOARD_TRACING.md), trace `trace-03520e9bb1d64456`.
- Span đáng chú ý: `rag_retrieve` 2,500 ms so với `llm_generate` 150 ms; đây là evidence trực tiếp cho bottleneck retrieval.

## 4. Prompt versioning

- Prompt name: `day13-chat`.
- Runtime baseline: label `production`, version `local-v1`, source `local`.
- Candidate/managed version: chưa có evidence vì không có Langfuse public/secret key trong môi trường.
- Trace ID local có metadata prompt: `trace-51771de9947c45ea`.
- Rollback: không làm giả thao tác rollback. Hướng dẫn thực hiện v1/v2, đổi label và rollback: [prompt-versioning status](evidence/PROMPT_VERSIONING_STATUS.md).

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: **HỢP LỆ: 6/6 panel**.
- Evidence dashboard: [dashboard snapshot](evidence/dashboard-runtime.html) hiển thị latency, traffic, errors, cost, tokens và quality; mặc định 60 phút, target refresh 30 giây.
- SLO: P95 latency ≤ 3,000 ms; error rate ≤ 2%; chi phí ngày ≤ USD 2.50; quality proxy ≥ 0.75. Lý do: bao phủ tốc độ, độ tin cậy, ngân sách và chất lượng thấy bởi người dùng.
- Alert rules và runbook: [config/alert_rules.yaml](../config/alert_rules.yaml), [docs/alerts.md](../docs/alerts.md).

## 6. Điều tra challenge

- Challenge ID: `day13-k3-observability-v1`.
- Triệu chứng từ metrics: P95 tăng **155 ms → 2,658 ms**, P99 2,658 ms, error rate 0.00%.
- Trace liên quan: `trace-03520e9bb1d64456`.
- Log/correlation ID liên quan: `req-49d31ab8`; `component_completed` của `rag_retrieve` lúc `2026-08-11T03:13:52.047491Z`, `latency_ms=2500`.
- Root cause: incident chính thức `rag_slow` thêm 2.5 s ở `app/mock_rag.py`; retrieval chiếm gần hết latency.
- Fix action: tắt path incident sau khi thu evidence; trong production, áp retrieval timeout và fallback an toàn.
- Preventive measure: alert P95, trace các span retrieval/LLM, và runbook Metrics → Traces → Logs. Chi tiết: [CP3 evidence](evidence/CP3_CHALLENGE.md).

## 7. Đóng góp cá nhân

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| A — API & Middleware | CP1 correlation ID middleware, request context, exception handler, response timing header | Pending local integration commit | ContextVar phải clear ở cả biên request để không lẫn dữ liệu người dùng. |
| B — Security Engineer | CP1 regex email/điện thoại/CCCD/thẻ/passport/address; recursive PII scrub và test | Pending local integration commit | Redact ở processor cuối giúp che cả payload nested và exception. |
| C — Metrics & Dashboard | `error_rate_pct`, dashboard 6 panel/spec, portable snapshot và test denominator | Pending local integration commit | Error rate phải chia cho request nhận vào, không chỉ request thành công. |
| D — SRE & Alerts Engineer | CP2 SLO, 3 alert symptom-based và runbook | Pending local integration commit | Alert cần nói về SLO/ảnh hưởng người dùng, không nói về cờ implementation. |
| E — QA & Chief Investigator | Load test, trace sub-component RAG/LLM, CP3 investigation và tổng hợp report/evidence | Pending local integration commit | So sánh span trong trace rồi xác thực bằng log cùng correlation ID. |

## 8. Trạng thái checkpoint

- CP0: hoàn thành sau khi khắc phục baseline thiếu log; xem [evidence](evidence/CP0_BASELINE.md).
- CP1: hoàn thành, validator log 100/100.
- CP2: dashboard/SLO/alert/local trace journal hoàn thành; managed Langfuse prompt v1/v2 và rollback cần credentials thật, không thể thay bằng evidence giả.
- CP3: hoàn thành với challenge chính thức, incident đã được disable lại.
- Hoàn tất nộp bài: cần một lệnh commit cục bộ được chủ repo cho phép; không có push nào được thực hiện.
