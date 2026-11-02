# Buổi 8 — Intent, slot và câu hỏi làm rõ

**Thời lượng gợi ý:** 2–3 giờ  
**Phụ thuộc:** Buổi 7  
**Đọc trước:** [`kientruc.md`](../../data/kientruc.md), mục 4.1, 4.2 B/C/E và schema tool ở mục 6

## Mục tiêu

Chuyển câu đã chuẩn hóa thành request duy nhất, có intent, bộ lọc cứng, sở thích, điều kiện loại trừ và trạng thái cần hỏi lại.

## Vì sao tạo request trước Agent?

Một request chuẩn là giao kèo giữa NLP, backend, catalog và Agent. Nếu mỗi module tự hiểu câu người dùng, điều kiện có thể bị đổi hoặc mất khi chuyển lớp.

## Các bước

1. **Tạo `nlp/intent.py`.** Nhận diện `recommend`, `search`, `detail`, `compare`, `browse`, `greeting`, `out_of_scope` theo luật rõ ràng.
2. **Không để các intent chồng lấn:** “máy nào dưới 5 triệu?” là search; “gợi ý máy dưới 5 triệu” là recommend; “liệt kê tất cả Samsung” là browse; câu hỏi model cụ thể là detail.
3. **Tạo `nlp/slots.py`.** Trích xuất hãng, model, min/max giá cùng inclusivity, thông số tối thiểu, tag cần có, tag loại trừ và ID loại trừ.
4. **Phân biệt bắt buộc/mềm:** mặc định tag là preference; cách nói “phải có/chỉ lấy” dùng `required_tags` hoặc `required_tag_groups`; “ưu tiên” dùng `preferences`.
5. **Tạo hàm validate request.** Kiểm tra intent hợp lệ, hãng/tag tồn tại, số không âm, min≤max và giới hạn 1–3 kết quả. Nếu hãng/model mâu thuẫn hoặc tên model khớp nhiều dòng thì trả trạng thái `needs_clarification`.
6. **Định nghĩa ánh xạ intent-tool:** recommend/search → `recommend_phones`; detail → `get_phone_detail`; compare → `compare_phones`; browse → `browse_phones`; greeting/out-of-scope không gọi tool.
7. **Viết ví dụ đầu vào/đầu ra có nhãn** cho câu có dấu, không dấu, tiếng lóng, phủ định và câu mơ hồ. Giữ một số câu chưa dùng để viết luật làm tập đánh giá sau này.

## Tệp cần tạo hoặc sửa

- `src/phone_advisor/nlp/intent.py`
- `src/phone_advisor/nlp/slots.py`
- `tests/test_nlp.py`
- `docs/huong_dan_tung_buoi/tap_cau_nlp.md` (tập phát triển riêng)

## Tự kiểm tra

- Request có cùng cấu trúc cho các câu đồng nghĩa.
- Điều kiện cứng không bị biến thành preference và ngược lại.
- Tên/giá mơ hồ không bị tự đoán; backend yêu cầu người dùng xác nhận.
- `dưới`, `tối đa`, `trên`, `ít nhất` tạo toán tử đúng.
- Greeting/out-of-scope không đi vào catalog.

## Hoàn thành khi

Một câu đầu vào tạo ra request đã chuẩn hóa hoặc một câu hỏi làm rõ; không có request nửa hợp lệ được gửi tới catalog.

**Đầu ra cuối buổi:** parser baseline có thể giải thích và kiểm tra riêng.


