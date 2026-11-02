# Buổi 9 — Quản lý state hội thoại theo phiên

**Thời lượng gợi ý:** 1,5–2 giờ  
**Phụ thuộc:** Buổi 8  
**Đọc trước:** [`kientruc.md`](../../data/kientruc.md), mục 4.2 E½ và 8

## Mục tiêu

Giữ điều kiện cần thiết giữa các lượt trong cùng phiên, hỗ trợ thêm/đổi/xóa điều kiện và không trộn hai cuộc hội thoại.

## Vì sao phải tách state khỏi lịch sử chat?

LLM chỉ cần vài lượt gần nhất làm ngữ cảnh, còn catalog cần các slot hiện hành. Lưu hai dạng riêng giúp giảm prompt và biết chính xác điều kiện nào đang được áp dụng.

## Các bước

1. **Tạo `nlp/dialogue_state.py`.** Định nghĩa state có filters, preferences, exclusions, `last_results` và thời điểm hết hạn.
2. **Giữ lịch sử tối đa 5 lượt riêng** với state có cấu trúc; không suy ra state chỉ bằng cách gửi toàn bộ hội thoại cho LLM.
3. **Cô lập state theo phiên.** Với bản local một tiến trình, dùng server-side store keyed bằng session ID ngẫu nhiên; cookie chỉ giữ ID. Không dùng một đối tượng hội thoại duy nhất cho mọi người dùng.
4. **Định nghĩa thao tác cập nhật:** câu mới bổ sung thì merge; câu đổi hãng/giá thì ghi đè trường tương ứng; câu rút lại preference thì xóa preference đó; “bắt đầu lại” xóa toàn bộ.
5. **Đặt TTL mặc định 30 phút không hoạt động** và cho phép cấu hình. Sau khi hết hạn, câu mới mở một state rỗng.
6. **Lưu `last_results` là ID** của các sản phẩm cuối cùng trong phiên; kiểm tra ID thuộc phiên trước khi hiểu “máy thứ hai” hoặc “hai máy vừa rồi”.
7. **Viết kiểm tra cho hai phiên đồng thời**, hết hạn, reset, merge, overwrite và removal.

## Tệp cần tạo hoặc sửa

- `src/phone_advisor/nlp/dialogue_state.py`
- `src/phone_advisor/config.py`
- `tests/test_agent_flow.py` hoặc `tests/test_dialogue_state.py`

## Tự kiểm tra

- “Tìm Samsung dưới 15 triệu” rồi “ưu tiên pin trâu” giữ Samsung/ngân sách và thêm preference.
- “Không cần pin nữa” xóa đúng preference pin.
- “Tìm Xiaomi thay Samsung” ghi đè hãng, không giữ Samsung như bộ lọc cũ.
- Hai session có state khác nhau; reset một session không xóa session còn lại.
- State hết hạn bị xóa và không làm rò kết quả cũ.

## Hoàn thành khi

Các lượt tiếp nối hoạt động đúng trong cùng phiên và không thể làm lộ state giữa các phiên.

**Đầu ra cuối buổi:** state manager có quy tắc merge/reset/expiry rõ.


