# Buổi 12 — API Flask cho chat

**Thời lượng gợi ý:** 2–2,5 giờ  
**Phụ thuộc:** Buổi 11  
**Đọc trước:** [`kientruc.md`](../../data/kientruc.md), mục 2, 8 và 9

## Mục tiêu

Tạo `POST /api/chat` làm ranh giới giữa giao diện và pipeline NLP → state → policy/tool → Agent → response.

## Vì sao API là lớp riêng?

Giao diện không nên kết nối trực tiếp PostgreSQL, biết prompt hoặc tự quyết định điều kiện. API giữ logic nghiệp vụ ở server và cho phép thay UI mà không viết lại catalog.

## Các bước

1. **Tạo `web/routes.py`** và đăng ký route trong app. Chỉ nhận JSON có trường `message` là chuỗi không rỗng, dưới giới hạn độ dài cấu hình.
2. **Nối pipeline theo thứ tự:** xác thực input → lấy session state → normalize/intent/slots → hỏi lại nếu mơ hồ → backend chọn tool → gọi tool/Agent → cập nhật state → trả response.
3. **Áp dụng response contract** từ kiến trúc: `status`, `reply`, `products`, `clarification`; không để route trả các shape khác nhau cho cùng loại kết quả.
4. **Chuẩn hóa HTTP status:** 200 cho câu trả lời và clarification, 422 cho request sai, 503 khi Ollama/catalog không sẵn sàng và không có fallback.
5. **Cấu hình session an toàn:** server-side store, session ID ngẫu nhiên, cookie `HttpOnly`/`SameSite`, `Secure` trên HTTPS, khóa từ môi trường, CSRF/origin check cho POST.
6. **Cấu hình CORS chỉ cho origin cần thiết.** Bản local bind `127.0.0.1`; không mở ra mạng LAN khi chưa có cấu hình bảo vệ tương ứng.
7. **Tách thông báo cho người dùng khỏi log.** Log mã lỗi và thông tin kỹ thuật tối thiểu; không log cookie, session ID hay toàn bộ lịch sử chat.
8. **Kiểm tra route** cho request đúng, body sai, message rỗng/quá dài, clarification, không có kết quả, fallback và dịch vụ lỗi.

## Tệp cần tạo hoặc sửa

- `src/phone_advisor/web/routes.py`
- `src/phone_advisor/app.py`
- `src/phone_advisor/config.py`
- `tests/test_agent_flow.py` hoặc `tests/test_routes.py`

## Tự kiểm tra

- Request sai không đi tới Ollama hoặc catalog.
- Response API đúng shape cho kết quả, clarification và lỗi.
- Hai cookie/session khác nhau không thấy lịch sử hoặc `last_results` của nhau.
- Khi Ollama tắt, response dùng fallback nếu catalog hoạt động.
- Không có traceback, path máy cá nhân hay secret trong JSON trả về.

## Hoàn thành khi

Có thể gọi API bằng `Invoke-RestMethod` hoặc REST client mà không cần giao diện.

**Đầu ra cuối buổi:** endpoint chat có hợp đồng ổn định.


