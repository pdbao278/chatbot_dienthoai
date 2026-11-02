# Buổi 6 — Gợi ý, xem chi tiết và so sánh

**Thời lượng gợi ý:** 2–2,5 giờ  
**Phụ thuộc:** Buổi 5  
**Đọc trước:** [`kientruc.md`](../../data/kientruc.md), mục 5.3 và 6.1–6.3

## Mục tiêu

Thêm ranking sở thích mềm, lấy chi tiết theo ID và so sánh 2–3 sản phẩm. Điều kiện cứng vẫn do bộ lọc database ở Buổi 5 quyết định.

## Vì sao đây là buổi riêng?

Lọc trả lời “máy nào được phép xuất hiện”; ranking trả lời “máy nào nên đứng trước”. Tách hai việc giúp giải thích được kết quả và không để sở thích vô tình lấn át giới hạn ngân sách.

## Các bước

1. **Viết `catalog/recommend.py`.** Gọi bộ lọc trước; chỉ xếp hạng tập đã lọc.
2. **Tính điểm preference:** mỗi mục có `any_of` được tính tối đa một lần nếu sản phẩm có ít nhất một tag trong nhóm; cộng `priority` của các mục khớp.
3. **Xếp tie-break rõ ràng:** điểm preference giảm dần; nếu người dùng ưu tiên pin thì `pin_mah` giảm dần, nếu yêu cầu màn hình mượt thì `tan_so_quet_hz` giảm dần; sau đó giá tăng dần rồi ID tăng dần. Không dùng megapixel để xếp chất lượng camera.
4. **Tạo lý do máy được chọn** từ điều kiện thực sự khớp, chẳng hạn “đúng hãng, trong ngân sách, có tag `pin_trau`”. Không viết “tốt nhất” nếu dữ liệu không chứng minh.
5. **Giới hạn gợi ý tối đa ba máy.** Nếu không có sở thích, giữ thứ tự giá tăng dần rồi ID; không giả vờ đó là xếp hạng chất lượng.
6. **Lấy chi tiết theo ID** bằng repository. Tên model được phân giải ở lớp NLP sau; catalog không tự chọn phiên bản gần đúng.
7. **Viết `catalog/compare.py`.** Nhận đúng 2 hoặc 3 ID; nếu thiếu bất kỳ ID nào thì trả lỗi/not-found cho toàn bộ yêu cầu, không so sánh một phần.
8. **Chỉ so sánh dữ liệu có thật.** Chip là tên mô tả; không kết luận mạnh/yếu nếu chưa có bảng benchmark chuẩn.

## Tệp cần tạo hoặc sửa

- `src/phone_advisor/catalog/recommend.py`
- `src/phone_advisor/catalog/compare.py`
- `src/phone_advisor/catalog/repository.py` (nếu cần hàm lấy theo ID)
- `tests/test_catalog.py`

## Tự kiểm tra

- Preference không làm sản phẩm vi phạm giá/hãng lọt vào kết quả.
- Preference không khớp làm điểm thấp hơn nhưng không tự loại sản phẩm.
- Mỗi nhóm `any_of` chỉ tính điểm một lần.
- Cùng đầu vào luôn trả cùng top 3 và cùng lý do.
- Compare giữ đúng thứ tự ID; trường trống trả `null`, không tự điền.

## Hoàn thành khi

Catalog có search, browse, recommend, detail và compare đủ để chạy mà không cần NLP hay Agent.

**Đầu ra cuối buổi:** luồng nghiệp vụ sản phẩm xác định và có thể giải thích.


