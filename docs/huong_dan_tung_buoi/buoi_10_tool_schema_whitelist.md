# Buổi 10 — Hợp đồng tool và whitelist

**Thời lượng gợi ý:** 2–2,5 giờ  
**Phụ thuộc:** Buổi 9  
**Đọc trước:** [`kientruc.md`](../../data/kientruc.md), mục 6.1–6.5

## Mục tiêu

Tạo ranh giới backend chặn tool ngoài phạm vi, request sai schema và lời gọi làm thay đổi điều kiện người dùng.

## Vì sao làm trước khi kết nối Ollama?

Không nên để model tự quyết định quyền truy cập catalog. Khi whitelist và kiểm tra request đã chạy được với lời gọi giả lập, tích hợp model chỉ còn là lớp giao tiếp.

## Các bước

1. **Tạo `agent/tool_schemas.py`.** Mô tả input/output của `recommend_phones`, `get_phone_detail`, `compare_phones`, `browse_phones` theo mục 6 của kiến trúc.
2. **Tạo `agent/tool_registry.py`.** Ánh xạ đúng bốn tên tool tới hàm catalog tương ứng; không dùng `eval`, import tùy ý hay tên hàm tự sinh từ model.
3. **Chọn tool bằng intent đã xác thực.** Mỗi lượt chỉ bật tool phù hợp intent; greeting/out-of-scope không bật tool nào.
4. **Validate ở biên backend:** kiểu/giá trị, hãng, tag, ID, inclusive flags, page size, limit và số ID compare. Không tin validation phía trình duyệt hoặc JSON do model trả về.
5. **So sánh đối số với request NLP chuẩn.** Từ chối nếu model bỏ hãng/ngân sách/tag bắt buộc, tự thêm tag, đổi ID hoặc nới điều kiện.
6. **Chuẩn hóa output và lỗi.** Thành công trả `status/items`; không có sản phẩm trả `not_found`; đầu vào sai trả `VALIDATION_ERROR`; lỗi dịch vụ trả `SERVICE_UNAVAILABLE` mà không lộ traceback.
7. **Chỉ cho tool đọc dữ liệu.** Tool không nhận đường dẫn file, câu lệnh SQL, truy vấn tự do hay thao tác ghi database.
8. **Viết kiểm tra xấu có chủ ý:** tool lạ, field thừa, tag lạ, giá âm, `min > max`, quá nhiều ID, ID không tồn tại và model bỏ điều kiện đã xác nhận.

## Tệp cần tạo hoặc sửa

- `src/phone_advisor/agent/tool_schemas.py`
- `src/phone_advisor/agent/tool_registry.py`
- `tests/test_agent_flow.py`

## Tự kiểm tra

- Tool không đúng intent bị từ chối.
- JSON hợp lệ về cú pháp nhưng sai nghiệp vụ cũng bị từ chối.
- Model không thể làm thay đổi bộ lọc cứng qua arguments.
- Không có đường gọi tới thao tác ghi/xóa file.
- Error response không tiết lộ stack trace hoặc đường dẫn máy.

## Hoàn thành khi

Tool registry chạy với lời gọi giả lập, chỉ chấp nhận hợp đồng đã định nghĩa và chỉ đọc catalog.

**Đầu ra cuối buổi:** lớp bảo vệ độc lập với Ollama.


