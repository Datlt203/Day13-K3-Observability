# Yêu cầu dashboard

Contract có thể kiểm tra bằng máy nằm tại `config/dashboard.yaml`. Hướng dẫn dựng và kiểm tra runtime nằm tại [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md).

Dashboard chính cần giám sát 6 nhóm thông tin quan trọng để đảm bảo độ tin cậy và hiệu năng của hệ thống AI:

1. **Latency:** Đo lường hiệu năng phản hồi với các chỉ số P50, P95, P99 (đơn vị: ms).
2. **Traffic:** Giám sát lưu lượng truy cập (số lượng yêu cầu mỗi phút).
3. **Error Rate:** Tỷ lệ lỗi và phân tích chi tiết các loại lỗi xảy ra.
4. **Cost:** Theo dõi chi phí sử dụng API theo thời gian (đơn vị: USD).
5. **Token Usage:** Tổng hợp token tiêu thụ cho cả đầu vào (input) và đầu ra (output).
6. **Quality Proxy:** Chỉ số đánh giá chất lượng phản hồi từ mô hình AI (thang điểm 0-1).

Tiêu chuẩn trình bày:

- Khoảng thời gian mặc định: 1 giờ.
- Tự refresh mỗi 15–30 giây nếu công cụ hỗ trợ.
- Thiết lập ngưỡng (threshold) hoặc đường mục tiêu (SLO) cho mỗi chỉ số.
- Ghi rõ đơn vị đo lường.
- Chỉ giữ 6–8 panel quan trọng ở lớp chính để đảm bảo khả năng quan sát.
- Screenshot evidence phải hiển thị rõ ràng tên panel và khoảng thời gian quan sát.

Kiểm tra contract trước khi chụp evidence:

```bash
python scripts/validate_dashboard.py
```
