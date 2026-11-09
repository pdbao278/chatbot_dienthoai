# Buổi 4 — Import CSV và xây repository PostgreSQL

**Thời lượng gợi ý:** 2–3 giờ  
**Phụ thuộc:** Buổi 3  
**Đọc trước:** [`kientruc.md`](../../data/kientruc.md), mục 5.1; [`mo_ta_du_lieu.md`](../mo_ta_du_lieu.md)

## Mục tiêu

Viết lệnh import có kiểm soát để biến CSV đầu vào thành dữ liệu PostgreSQL, sau đó tạo repository cho catalog truy vấn database. Sau buổi này, web lấy sản phẩm từ PostgreSQL và không cần mở file CSV để phục vụ câu hỏi.

## Vì sao seed phải là lệnh riêng?

Import là một tác vụ thay đổi dữ liệu; nếu tự chạy mỗi lần ứng dụng khởi động, app có thể ghi đè chỉnh sửa, nhập trùng hoặc xóa dữ liệu. Tách seed riêng giúp bạn quyết định khi nào nhập, có thể xem trước số dòng và giữ luồng web gần cách triển khai thật.

## Các bước

1. **Chọn chính sách import.** Mặc định cho phép seed lần đầu khi bảng `products` đang rỗng; nếu đã có sản phẩm, dừng và báo rõ. Chỉ cho phép cập nhật bản ghi trùng ID khi người chạy truyền `--upsert`. Không xóa database rows chỉ vì ID vắng trong CSV mới.
2. **Tạo lệnh CLI** `scripts/seed_catalog.py`, chạy bằng lệnh có cấu hình rõ ràng, ví dụ `python -m scripts.seed_catalog --csv data/dien_thoai_chuan_hoa.csv`. Không gọi script này trong app factory, khi import module, hoặc ở `GET /health`.
3. **Đọc CSV bằng `csv.DictReader`.** Dùng đường dẫn cấu hình/đối số CLI thay vì đường dẫn `E:\...` gắn cứng. Kiểm tra header theo data dictionary; kiểm tra ID không rỗng/trùng, trường số hợp lệ và tag thuộc tập dữ liệu.
4. **Chuyển kiểu trước khi mở transaction ghi.** Chuẩn hóa ID và số; ô tùy chọn thành `None`; tách `tags_nhu_cau` bằng dấu phẩy, trim khoảng trắng và chuẩn hóa slug. Thu thập lỗi theo dòng CSV để thông báo lỗi có số dòng/cột, không lặng lẽ bỏ hàng sai.
5. **Ánh xạ một dòng vào model.** Giữ nguyên ID nguồn làm `Product.id`; giữ giá theo số nguyên VND. Với mỗi tag, lấy hoặc tạo bản ghi `Tag`, rồi liên kết qua `product_tags`. Không lưu nguyên chuỗi tags vào `Product`.
6. **Ghi theo transaction.** Nếu một sản phẩm lỗi, rollback toàn bộ lần import để không có catalog nạp dở. Chỉ commit sau khi mọi dòng và quan hệ tag hợp lệ. Với dữ liệu 162 dòng, một transaction đơn giản là đủ. Sau khi chèn ID nguồn, đồng bộ identity/sequence tới ID lớn nhất để lần thêm sản phẩm mới không đụng khóa chính.
7. **In báo cáo sau import.** Hiển thị số dòng đọc, số sản phẩm tạo/cập nhật, số tag và thông báo lỗi. Không in `DATABASE_URL` hoặc mật khẩu ra console/log.
8. **Viết catalog repository** trong `src/phone_advisor/catalog/repository.py`. Hàm truy xuất theo ID, lọc hãng/giá/RAM/ROM/pin và join tag dùng SQLModel `select()`. Dùng điều kiện so sánh số và slug tag chính xác; không dùng substring tìm trên chuỗi tag.
9. **Giữ phạm vi quyền.** Repository của Agent chỉ cung cấp phương thức đọc catalog. Nếu có thao tác sửa sản phẩm cho đồ án, để ở route/quy trình quản trị riêng, không đưa quyền ghi vào tool của Agent.
10. **Thử lại lần seed thứ hai và đường chạy web.** Lần thứ hai không có `--upsert` phải dừng an toàn; có cờ cập nhật thì chỉ cập nhật/tạo theo chính sách đã chọn. Sau đó tạm đổi tên CSV và khởi động web: app vẫn phải truy vấn được từ PostgreSQL. Khôi phục tên file sau khi kiểm tra.

## Tệp cần tạo hoặc sửa

- `scripts/seed_catalog.py`
- `src/phone_advisor/catalog/repository.py`
- `src/phone_advisor/config.py`
- `src/phone_advisor/db/models.py` nếu cần chỉnh ánh xạ

## Tự kiểm tra

- Số `products` trong database bằng số sản phẩm hợp lệ của CSV; ID không trùng.
- Tag mẫu như `choi_game` xuất hiện một lần trong `tags` và nối tới đúng các sản phẩm qua `product_tags`.
- Truy vấn theo ID, hãng và giá đọc từ PostgreSQL; không có loader CSV trong đường xử lý request.
- CSV thiếu cột, ID trùng hoặc giá sai khiến seed báo dòng lỗi và rollback.
- Chạy lại seed không tự ghi đè; hành vi `--upsert` được ghi rõ trong help của CLI.
- Web vẫn trả được catalog nếu file CSV seed không hiện diện sau lần import.

## Hoàn thành khi

CSV chỉ còn là đầu vào của lệnh import; PostgreSQL giữ dữ liệu bền vững và repository là đường duy nhất để catalog đọc dữ liệu runtime.

**Đầu ra cuối buổi:** dữ liệu sản phẩm/tag đã có trong PostgreSQL, lệnh seed an toàn và repository truy vấn được.
