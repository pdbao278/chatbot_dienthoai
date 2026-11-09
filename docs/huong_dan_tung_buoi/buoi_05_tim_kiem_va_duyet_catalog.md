# Buổi 5 — Tìm kiếm và duyệt catalog

**Thời lượng gợi ý:** 2–2,5 giờ  
**Phụ thuộc:** Buổi 4  
**Đọc trước:** [`kientruc.md`](../../data/kientruc.md), mục 5.2 và 6.4

## Mục tiêu

Viết chức năng lọc sản phẩm theo điều kiện bắt buộc và chức năng duyệt danh sách có phân trang. Cả hai phải cho cùng một đầu vào thì trả cùng kết quả và thứ tự.

## Vì sao làm bộ lọc trước ranking?

Ranking không được phép sửa kết quả lọc. Khi kiểm tra riêng search, ta chứng minh được máy nào thỏa hãng, giá và thông số trước khi thêm sở thích hoặc LLM.

## Các bước

1. **Định nghĩa hàm truy vấn** trong `catalog/search.py`: nhận một repository/session cùng `filters`, tạo câu truy vấn SQLModel `select()` để database lọc tập ứng viên.
2. **Áp dụng mọi điều kiện cứng bằng AND:** hãng nếu có, min/max giá, RAM/ROM/pin/tần số tối thiểu, `required_tags`, từng nhóm `required_tag_groups`, hãng/tag/ID bị loại trừ.
3. **Dùng toán tử giá chính xác:** `dưới 15 triệu` là `<`; `tối đa 15 triệu` là `<=`; `trên 10 triệu` là `>`; `ít nhất 10 triệu` là `>=`. Nếu hai đầu bằng nhau, chỉ còn kết quả khi cả hai đầu bao gồm ngưỡng.
4. **So tag theo tập đã tách.** `required_tags` là AND; trong một `required_tag_group` là OR; sản phẩm có bất kỳ tag bị loại nào thì loại.
5. **Sắp kết quả ổn định** theo giá tăng dần rồi ID tăng dần trong câu truy vấn. Không để thứ tự phụ thuộc thứ tự database trả dòng nếu thiếu `ORDER BY`.
6. **Viết `catalog/browse.py`.** Dùng bộ lọc hãng/giá, nhận `page` và `page_size`, trả `items`, `total`, trang hiện tại và danh sách hãng phân biệt.
7. **Giới hạn phân trang** ở `page_size` tối đa 20; page bắt đầu từ 1. `search`/`recommend` chỉ trả tối đa 3, còn yêu cầu liệt kê nhiều thì chuyển sang browse.
8. **Viết các ca kiểm tra ranh giới giá** với đúng ngưỡng, nhỏ hơn một đơn vị và lớn hơn một đơn vị.

## Tệp cần tạo hoặc sửa

- `src/phone_advisor/catalog/search.py`
- `src/phone_advisor/catalog/browse.py`

Các hàm truy vấn nhận session/repository theo tham số để vòng đời session do tầng request quản lý; không tạo session toàn cục bên trong module.
- `tests/test_catalog.py`

## Tự kiểm tra

- Máy giá đúng 15.000.000đ bị loại với “dưới 15 triệu”, nhưng được giữ với “tối đa 15 triệu”.
- Kết quả không chứa hãng bị loại, tag bị loại hoặc thông số thấp hơn mức bắt buộc.
- Tag không bị khớp nhầm bằng substring.
- Duyệt trang 1 rồi trang 2 không lặp ID; `total` không đổi.
- Kết quả cùng truy vấn luôn cùng thứ tự.

## Hoàn thành khi

Search lọc đúng mọi điều kiện bắt buộc và browse liệt kê đủ catalog qua nhiều trang.

**Đầu ra cuối buổi:** bộ lọc xác định và danh mục có phân trang, chưa có LLM.


