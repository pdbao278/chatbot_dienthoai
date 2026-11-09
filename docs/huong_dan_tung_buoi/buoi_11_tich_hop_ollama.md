# Buổi 11 — Tích hợp Agent và Ollama

**Thời lượng gợi ý:** 2–3 giờ  
**Phụ thuộc:** Buổi 10  
**Đọc trước:** [`kientruc.md`](../../data/kientruc.md), mục 6.6 và 9

## Mục tiêu

Kết nối Ollama để Agent gọi đúng tool đã được backend chọn, sau đó diễn đạt kết quả catalog bằng tiếng Việt. Khi Ollama lỗi, ứng dụng vẫn có câu trả lời dự phòng.

## Vì sao chỉ tích hợp ở giai đoạn này?

Catalog, parser và schema đã có thể kiểm tra riêng. Khi thêm LLM lúc này, ta dễ phân biệt lỗi hiểu ngôn ngữ, lỗi tool và lỗi truy vấn, đồng thời giới hạn được quyền của model.

## Các bước

1. **Ghi cấu hình model và timeout** trong `config.py`/biến môi trường; không ghi tên model rải rác hoặc secret trong prompt.
2. **Kiểm tra Ollama sẵn sàng** và model đã cấu hình có thể trả một câu đơn giản. Nếu lỗi, dừng buổi ở đây để xử lý kết nối trước khi viết orchestration.
3. **Tạo `agent/orchestrator.py`.** Đầu vào là request đã xác thực và lịch sử tối đa 5 lượt; không gửi toàn bộ CSV.
4. **Chỉ cung cấp tool được backend bật** cho intent hiện tại. Tool arguments phải khớp request chuẩn; registry ở Buổi 10 mới là nơi thực thi.
5. **Dùng system prompt** ở mục 6.6: chỉ dữ liệu từ tool, không tự đổi điều kiện, không bịa, không tạo HTML/JavaScript.
6. **Giới hạn vòng gọi tool tối đa 2 lần** trong một lượt. Nếu model lặp, gọi tool sai hoặc JSON sai thì dừng, không thử vô hạn.
7. **Đặt timeout hữu hạn** cho Ollama và bắt các lỗi kết nối/model chưa sẵn sàng. Không để request FastAPI treo vô hạn.
8. **Viết fallback có mẫu cố định:** khi catalog đã có kết quả nhưng Ollama lỗi, backend dựng câu trả lời ngắn từ ProductCard; nếu catalog cũng lỗi, trả lỗi dịch vụ có kiểm soát.
9. **Kiểm tra chống prompt injection** bằng câu yêu cầu bỏ quy tắc hoặc nội dung CSV có câu giống chỉ dẫn; kết quả vẫn phải theo whitelist và request chuẩn.

## Tệp cần tạo hoặc sửa

- `src/phone_advisor/agent/orchestrator.py`
- `src/phone_advisor/agent/prompts/` (prompt hệ thống)
- `src/phone_advisor/config.py`
- `tests/test_agent_flow.py`

## Tự kiểm tra

- Recommend/search/detail/compare/browse chỉ gọi tool tương ứng intent.
- Câu hỏi mơ hồ được hỏi lại trước khi gọi tool.
- Không có tool-call loop quá hai lượt.
- Ollama timeout không làm server treo; fallback dùng đúng trường catalog.
- Prompt injection không đổi giá, hãng, tag, ID hay whitelist.

## Hoàn thành khi

LLM chỉ điều phối/diễn đạt trên request và kết quả có cấu trúc; catalog vẫn là nguồn sự thật.

**Đầu ra cuối buổi:** Agent dùng được với Ollama và có đường lui khi model lỗi.


