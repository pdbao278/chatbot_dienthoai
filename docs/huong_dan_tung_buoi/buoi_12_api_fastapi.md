# Buổi 12 — API FastAPI cho chat

**Thời lượng gợi ý:** 2–2,5 giờ  
**Phụ thuộc:** Buổi 11  
**Đọc trước:** [`kientruc.md`](../../data/kientruc.md), mục 2, 8 và 9

## Mục tiêu

Tạo endpoint `POST /api/chat` bằng FastAPI (dùng Pydantic validation và hỗ trợ mở rộng StreamingResponse) làm ranh giới giữa giao diện và pipeline NLP → state → policy/tool → Agent → response.

## Vì sao API là lớp riêng?

Giao diện không nên kết nối trực tiếp PostgreSQL, biết prompt hoặc tự quyết định điều kiện. API giữ logic nghiệp vụ ở server và cho phép thay đổi giao diện (Web, Mobile) mà không cần viết lại catalog hay pipeline AI.

## Các bước

1. **Tạo `web/routes.py`** dùng `APIRouter` của FastAPI. Định nghĩa Pydantic schema cho request body:
   ```python
   from pydantic import BaseModel, Field

   class ChatRequest(BaseModel):
       message: str = Field(..., min_length=1, max_length=500)
   ```
2. **Nối pipeline theo thứ tự:** 
   * Xác thực input tự động bằng Pydantic model.
   * Lấy session state từ cookie hoặc session header.
   * Gọi bộ phân tích NLP (`normalize` $\rightarrow$ `intent` $\rightarrow$ `slots`).
   * Nếu mơ hồ / mâu thuẫn $\rightarrow$ trả `needs_clarification`.
   * Backend chọn tool whitelist $\rightarrow$ gọi Agent (Ollama) $\rightarrow$ cập nhật state $\rightarrow$ trả response.
3. **Áp dụng response contract** từ kiến trúc:
   ```python
   class ChatResponse(BaseModel):
       status: str
       reply: str
       products: list = []
       clarification: str | None = None
   ```
4. **Hỗ trợ Streaming Response (Tùy chọn nâng cao):** Có thể mở rộng endpoint `POST /api/chat/stream` trả về `StreamingResponse` với `media_type="text/event-stream"` để chữ chạy theo thời gian thực (SSE).
5. **Chuẩn hóa HTTP status:** 200 cho câu trả lời và clarification, 422 do FastAPI tự động trả về khi body sai schema, 503 khi Ollama/catalog không sẵn sàng và không có fallback.
6. **Cấu hình Middleware an toàn:**
   * Bật `CORSMiddleware` chỉ cho phép origin cần thiết (local bind `127.0.0.1:8000`).
   * Cấu hình cookie session an toàn: `HttpOnly`, `SameSite="lax"`, `Secure` trên HTTPS.
7. **Tách thông báo cho người dùng khỏi log:** Log mã lỗi và thông tin kỹ thuật tối thiểu; không log cookie, session ID hay toàn bộ lịch sử chat.
8. **Kiểm tra tương tác trên Swagger UI:** Truy cập `http://127.0.0.1:8000/docs` để gửi thử các request đúng, request rỗng (kiểm tra lỗi 422), clarification và fallback.

## Tệp cần tạo hoặc sửa

- `src/phone_advisor/web/routes.py`
- `src/phone_advisor/app.py`
- `src/phone_advisor/config.py`
- `tests/test_agent_flow.py` hoặc `tests/test_routes.py`

## Tự kiểm tra

- Request sai schema bị FastAPI tự động chặn ở tầng gateway (trả mã 422), không đi tới Ollama hoặc catalog.
- Response API đúng định dạng JSON contract cho kết quả, clarification và lỗi.
- Xem và gửi thử nghiệm được trên Swagger UI `/docs`.
- Hai cookie/session khác nhau không thấy lịch sử hoặc `last_results` của nhau.
- Khi Ollama tắt, response tự động kích hoạt fallback nếu catalog hoạt động.
- Không có traceback, đường dẫn máy cá nhân hay secret trong JSON trả về.

## Hoàn thành khi

Có thể gọi API bằng Swagger UI (`/docs`), `Invoke-RestMethod` hoặc REST client mà không cần giao diện.

**Đầu ra cuối buổi:** endpoint chat FastAPI có hợp đồng ổn định và tài liệu OpenAPI tự động.

