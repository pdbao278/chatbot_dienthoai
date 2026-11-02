# Buổi 2 — Kiểm tra dữ liệu sản phẩm

**Thời lượng gợi ý:** 1,5–2 giờ  
**Phụ thuộc:** Buổi 1  
**Đọc trước:** [`kientruc.md`](../../data/kientruc.md), mục 1, 5.1 và 12

## Mục tiêu

Xác nhận CSV có thể dùng làm dữ liệu seed ban đầu, ghi lại kiểu dữ liệu và trường hợp thiếu/sai trước khi viết lệnh import vào PostgreSQL.

## Vì sao làm trước catalog?

Catalog chỉ có thể trả lời đúng nếu hiểu rõ cột, đơn vị và tag. Kiểm tra dữ liệu sớm tránh viết bộ lọc dựa trên giả định sai rồi phải sửa nhiều module.

## Các bước

1. **Xác nhận vai trò file.** `data/dien_thoai_chuan_hoa.csv` là đầu vào seed ban đầu; PostgreSQL mới là nguồn dữ liệu runtime sau buổi import. JSON hiện có chỉ là bản tham chiếu/bản xuất.
2. **Đếm dòng và đọc header** bằng PowerShell:

   ```powershell
   $rows = Import-Csv -LiteralPath .\data\dien_thoai_chuan_hoa.csv -Encoding UTF8
   $rows.Count
   $rows[0].PSObject.Properties.Name
   ```

3. **Kiểm tra ID trùng/rỗng và các trường bắt buộc** (`id`, `ten_san_pham`, `hang`, `gia_ban`, `ram_gb`, `rom_gb`, `pin_mah`, `tags_nhu_cau`). Ghi lại mọi dòng lỗi; không sửa âm thầm dữ liệu gốc.
4. **Kiểm tra kiểu và đơn vị:** `gia_ban` là VND; RAM/ROM là GB; pin là mAh; tần số là Hz; tags là các giá trị phân cách bằng dấu phẩy.
5. **Liệt kê hãng và tag duy nhất.** So sánh với danh sách trong mục 4.2 D của kiến trúc; kiểm tra chính tả tag và tag có khoảng trắng thừa.
6. **Kiểm tra trường tùy chọn** như chip, camera, ảnh và URL. Ghi rõ trường nào có thể rỗng; không giả định URL hợp lệ chỉ vì ô có nội dung.
7. **Đối chiếu và cập nhật** `docs/mo_ta_du_lieu.md`: số dòng/cột, mô tả từng cột, đơn vị, tag, quy tắc thiếu dữ liệu và các bất thường. Số liệu trong mẫu là snapshot; kiểm tra lại thay vì mặc định vẫn đúng.

## Tệp cần tạo hoặc sửa

- `docs/mo_ta_du_lieu.md`
- Chưa sửa CSV trong buổi này. Nếu phát hiện dữ liệu sai, ghi ID và nội dung vấn đề để xử lý riêng.

## Tự kiểm tra

- Đếm số dòng/cột đúng với file hiện tại; không ghi số liệu cũ nếu CSV đã thay đổi.
- ID bắt buộc duy nhất và không rỗng.
- Giá và thông số số học đọc được; nếu có ngoại lệ thì được ghi lại.
- Tag được liệt kê theo phần tử chính xác, không phải dò chuỗi con.
- Tài liệu phân biệt rõ trường bắt buộc với trường có thể thiếu.

## Hoàn thành khi

Có một mô tả dữ liệu đủ để người khác viết repository mà không phải đoán đơn vị hoặc ý nghĩa cột.

**Đầu ra cuối buổi:** data dictionary và danh sách bất thường cần giải quyết.

