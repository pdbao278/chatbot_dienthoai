# Buổi 13 — Giao diện chat và thẻ sản phẩm

**Thời lượng gợi ý:** 2–3 giờ  
**Phụ thuộc:** Buổi 12  
**Đọc trước:** [`kientruc.md`](../../data/kientruc.md), mục 8

## Mục tiêu

Tạo giao diện tối thiểu để nhập câu hỏi, xem hội thoại, đọc tối đa ba product card và trả lời câu hỏi làm rõ.

## Vì sao làm giao diện sau API?

API đã định nghĩa response; UI chỉ cần hiển thị response đó. Cách này tránh để logic lọc/định dạng dữ liệu sản phẩm bị lặp trong JavaScript.

## Các bước

1. **Tạo trang chat** trong `web/templates/` và stylesheet/script trong `web/static/`.
2. **Làm luồng gửi câu hỏi:** disable nút khi đang chờ, hiển thị trạng thái đang xử lý, gọi `POST /api/chat` với JSON và giữ cookie session.
3. **Hiển thị loại response theo `status`:** tin nhắn bình thường, câu hỏi clarification, lỗi có thể thử lại; không đưa lỗi nội bộ lên màn hình.
4. **Tạo product card** chỉ dùng trường trong `ProductCard`: tên, hãng, giá database, RAM/ROM, chip, pin, tag khớp và ảnh/link nếu hợp lệ.
5. **Escape toàn bộ text.** Dùng render text an toàn của template/framework; tuyệt đối không đưa user/LLM/dữ liệu database vào `innerHTML` hoặc cơ chế `safe`.
6. **Kiểm tra URL ở server và UI:** chỉ dùng HTTPS thuộc domain allowlist; ảnh lỗi thì hiện placeholder; link ngoài mở tab mới có `noopener noreferrer`.
7. **Thêm thao tác tiện dụng** vừa đủ: gửi bằng Enter, xuống dòng bằng Shift+Enter, hiển thị lỗi mạng và không xóa lịch sử khi request thất bại.
8. **Kiểm tra màn hình hẹp và bàn phím:** form có label, focus rõ, thông báo trạng thái đọc được và card không tràn ngang.

## Tệp cần tạo hoặc sửa

- `src/phone_advisor/web/templates/`
- `src/phone_advisor/web/static/`
- `src/phone_advisor/web/routes.py` nếu cần bổ sung dữ liệu hiển thị

## Tự kiểm tra

- Gửi câu hỏi và nhận card từ API thật.
- Clarification hiện như câu hỏi tiếp nối; câu trả lời tiếp theo dùng đúng session.
- URL sai domain hoặc không phải HTTPS không tạo link/ảnh.
- Thẻ không hiện giá/thông số tự bịa khi field `null`.
- Chuỗi `<script>` trong câu hỏi/kết quả được hiển thị như text, không chạy.

## Hoàn thành khi

Người dùng hoàn tất được luồng hỏi → xem gợi ý → trả lời clarification → xem kết quả mà UI không tự xử lý nghiệp vụ.

**Đầu ra cuối buổi:** demo UI tối thiểu hoạt động trên desktop và màn hình hẹp.


