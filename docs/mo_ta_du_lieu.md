# Mô tả dữ liệu sản phẩm

**Nguồn nhập ban đầu:** `data/dien_thoai_chuan_hoa.csv`  
**Kiểm tra lần gần nhất:** 31/10/2026  
**Quy tắc:** PostgreSQL là nguồn dữ liệu chuẩn khi ứng dụng chạy. CSV chỉ được nạp qua lệnh seed tường minh; `data/dien_thoai_chuan_hoa.json` là bản tham chiếu/xuất, không được dùng để bổ sung dữ liệu runtime.

## Tổng quan hiện tại

- 162 dòng sản phẩm và 17 cột.
- ID không rỗng, không trùng trong lần kiểm tra gần nhất.
- Các cột hiện không có ô trống; các trường số kiểm tra được đều chuyển đổi được.
- Giá dùng VND; RAM/ROM GB; pin mAh; công suất sạc W; màn hình inch; tần số Hz.
- URL/ảnh hiện có giá trị ở mọi dòng, nhưng ứng dụng vẫn phải kiểm tra URL trước khi hiển thị.
- Hãng trong dữ liệu: Apple, HONOR, Motorola, Nothing Phone, Nubia, OPPO, realme, Samsung, Tecno, vivo, Xiaomi.

> Các số liệu trên là ảnh chụp tại ngày kiểm tra, không phải ràng buộc vĩnh viễn. Buổi 2 cần kiểm tra lại nếu CSV đã thay đổi; Buổi 4 đối chiếu số liệu sau khi seed vào database.

## Mô tả cột

| Cột | Kiểu dự kiến | Đơn vị/ý nghĩa | Bắt buộc | Ghi chú |
|---|---|---|---|---|
| `id` | số nguyên | Khóa sản phẩm | Có | Giữ nguyên ID từ CSV làm khóa chính trong `products` |
| `ten_san_pham` | chuỗi | Tên thương mại và phiên bản | Có | Dùng đối chiếu alias model |
| `hang` | chuỗi/category | Hãng | Có | Chuẩn hóa khi so khớp, giữ nguyên để hiển thị |
| `gia_ban` | số nguyên | VND | Có | Import vào PostgreSQL; giá snapshot, không đảm bảo là giá hiện tại |
| `he_dieu_hanh` | chuỗi | Hệ điều hành | Có ở snapshot hiện tại | Không dùng để suy ra phiên bản cập nhật |
| `chip_cpu` | chuỗi | Mô tả chip | Có ở snapshot hiện tại | Không dùng để kết luận mạnh/yếu nếu không có benchmark |
| `ram_gb` | số nguyên | GB | Có | Điều kiện lọc tối thiểu khi người dùng yêu cầu |
| `rom_gb` | số nguyên | GB | Có | Bản 1TB lưu theo giá trị GB trong CSV |
| `pin_mah` | số nguyên | mAh | Có | Có thể dùng để xếp hạng khi user ưu tiên pin |
| `sac_w` | số nguyên | W | Có ở snapshot hiện tại | Công suất sạc ghi trong dữ liệu |
| `man_hinh_inch` | số thực | inch | Có ở snapshot hiện tại | Giữ kiểu số thực |
| `tan_so_quet_hz` | số nguyên | Hz | Có ở snapshot hiện tại | Tool schema dùng tên `min_refresh_rate_hz` để lọc cột này |
| `camera_sau_mp` | số nguyên | MP | Có ở snapshot hiện tại | Không dùng MP làm đại diện cho chất lượng ảnh |
| `camera_truoc_mp` | số nguyên | MP | Có ở snapshot hiện tại | Chỉ dùng để so đúng trường số liệu |
| `tags_nhu_cau` | chuỗi phân cách dấu phẩy | Tag nhu cầu | Có | Tách thành tập tag, so khớp chính xác |
| `hinh_anh` | URL | Ảnh sản phẩm | Có giá trị hiện tại | Chỉ hiển thị HTTPS thuộc domain allowlist cấu hình |
| `url` | URL | Trang sản phẩm | Có giá trị hiện tại | Chỉ mở HTTPS thuộc domain allowlist cấu hình |

## Tag hiện có

`5g`, `chip_gaming`, `choi_game`, `chup_anh_dep`, `doanh_nhan`, `flagship`, `hoc_sinh_sinh_vien`, `hong_ngoai`, `man_hinh_muot`, `nfc`, `pin_khung`, `pin_trau`, `sac_nhanh`, `selfie_dep`, `thiet_ke_gap`.

Tag được xem là nhãn dữ liệu, không phải benchmark hay khẳng định chất lượng khách quan. Khi seed, tách tag thành bảng `tags` và bảng liên kết `product_tags`; không tìm tag bằng chuỗi con. Khi CSV thay đổi, kiểm tra danh sách tag và ngưỡng `pin_trau`/`pin_khung`.

## Quy tắc seed và cập nhật dữ liệu

1. Trước khi import, kiểm tra header, ID duy nhất, ô trống, kiểu số, tag và URL; lỗi phải nêu số dòng/cột.
2. Chạy migration Alembic trước khi seed; seed là lệnh riêng, tuyệt đối không tự chạy ở lúc Flask khởi động hoặc khi có request.
3. Mặc định chỉ seed database đang rỗng. Cập nhật record trùng ID chỉ khi dùng chế độ upsert có chủ đích; không xóa record vắng khỏi CSV mới nếu chưa quyết định chính sách xóa.
4. Không đổi đơn vị hoặc ý nghĩa cột mà không sửa model/migration và tài liệu.
5. Nếu cần JSON tham chiếu, sinh lại theo quy trình có ghi nhận; không sửa riêng một bản rồi quên bản còn lại.
6. Ghi ngày lấy/cập nhật giá trong metadata nếu biết. Nếu không có ngày, bot không được tự nêu ngày.

## Ánh xạ khi import

Mỗi dòng CSV tạo một `products` row, giữ nguyên `id`. Giá lưu theo VND, thông số lưu theo đơn vị trong bảng mô tả. `tags_nhu_cau` được tách dấu phẩy và chuyển thành các quan hệ `products` ↔ `tags` qua `product_tags`. Các endpoint/catalog chỉ truy vấn PostgreSQL; không đọc CSV hoặc JSON trong lúc phục vụ web.

