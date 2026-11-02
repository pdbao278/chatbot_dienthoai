# Buổi 14 — Đánh giá và chuẩn bị demo

**Thời lượng gợi ý:** 2–3 giờ  
**Phụ thuộc:** Buổi 13  
**Đọc trước:** [`kientruc.md`](../../data/kientruc.md), mục 10–12

## Mục tiêu

Đo chất lượng NLP và tư vấn trên câu chưa dùng để phát triển luật, xử lý các lỗi cuối và viết hướng dẫn chạy/demo để người khác có thể lặp lại.

## Vì sao cần tập đánh giá riêng?

Nếu chỉ thử bằng những câu đã dùng để viết luật, kết quả đẹp nhưng không cho biết bot có hiểu câu mới hay không. Đánh giá riêng giúp phân biệt lỗi parser, catalog, ranking và câu trả lời LLM.

## Các bước

1. **Lập tập câu có nhãn** trong `evaluation/intent_slots.csv` hoặc định dạng rõ tương đương. Mỗi câu có intent, hãng, biên giá/inclusivity, thông số, required tags, preferences và exclusions.
2. **Tách tập phát triển và tập đánh giá trước khi tinh chỉnh luật.** Không dùng câu đánh giá để thêm alias rồi vẫn báo đó là kết quả độc lập.
3. **Đo intent và slot** bằng accuracy cho intent và precision/recall/F1 cho slot quan trọng. Ghi rõ cách tính và ngưỡng đạt đã chọn trước.
4. **Kiểm tra điều kiện cứng riêng.** Tỷ lệ vi phạm hãng/giá/thông số/tag bắt buộc phải bằng 0 trên bộ tình huống kiểm tra; lỗi loại này không được bù bởi điểm NLP trung bình.
5. **Đánh giá top 3 bằng rubric** đã công bố: đáp ứng filters, khớp preferences, lý do dựa trên dữ liệu, không bịa. Lưu ví dụ đạt và chưa đạt.
6. **Đo thời gian chạy** riêng cho khởi động, catalog, Ollama warm/cold nếu có thể; ghi model/cấu hình dùng để phép đo có thể lặp lại.
7. **Chạy lại bộ kiểm tra lỗi**: CSV seed lỗi, database không kết nối, không kết quả, tên model mơ hồ, điều kiện giá xung đột, Ollama offline, session hết hạn và chuỗi HTML độc hại.
8. **Viết kịch bản demo 5–7 phút:** tìm đủ điều kiện, câu tiếp nối, model nhiều ROM, không có kết quả, duyệt phân trang và một ví dụ Ollama offline/fallback.
9. **Cập nhật README dự án:** cài môi trường, cấu hình PostgreSQL/`DATABASE_URL` và Ollama/model, cách migrate, seed dữ liệu, chạy app, vị trí CSV seed và giới hạn dữ liệu/giá.

## Tệp cần tạo hoặc sửa

- `evaluation/intent_slots.csv`
- `evaluation/` báo cáo kết quả hoặc biểu đồ cần nộp
- `README.md`
- `docs/mo_ta_du_lieu.md` nếu phát hiện cột/giới hạn cần làm rõ

## Tự kiểm tra

- Bộ đánh giá tách khỏi câu dùng phát triển luật.
- Báo cáo có cả số đo và lỗi tiêu biểu; không chỉ đưa ví dụ thành công.
- Tỷ lệ vi phạm điều kiện cứng bằng 0 trong các tình huống kiểm tra.
- Có thể chạy demo theo README trên cùng máy sau khi khởi động lại ứng dụng.
- Giới hạn về giá snapshot, chip và bảo hành được trình bày đúng.

## Hoàn thành khi

Có thể giải thích bot làm gì, đo được các lỗi chính và người khác chạy lại được demo theo hướng dẫn.

**Đầu ra cuối buổi:** báo cáo đánh giá và kịch bản demo hoàn chỉnh.


