# Buổi 3 — Dựng PostgreSQL và thiết kế schema

**Thời lượng gợi ý:** 2–3 giờ  
**Phụ thuộc:** Buổi 2  
**Đọc trước:** [`kientruc.md`](../../data/kientruc.md), mục 3, 5.1 và 9; [`mo_ta_du_lieu.md`](../mo_ta_du_lieu.md)

## Mục tiêu

Cài/cấu hình PostgreSQL local, tạo database và tài khoản ứng dụng, khai báo model SQLAlchemy và tạo migration đầu tiên bằng Alembic. Cuối buổi database có schema nhưng chưa cần nạp sản phẩm.

## Vì sao làm schema trước khi import?

CSV là dữ liệu đầu vào có cấu trúc cố định. Database cần kiểu dữ liệu và ràng buộc rõ để từ chối ID trùng, giá sai hoặc tag không thuộc sản phẩm. Tạo schema trước giúp lệnh import có đích đến ổn định; migration giúp dựng lại cùng cấu trúc trên máy khác mà không tạo bảng thủ công.

## Các bước

1. **Kiểm tra PostgreSQL.** Xác nhận dịch vụ PostgreSQL đang chạy và `psql --version` hoạt động. Nếu dùng pgAdmin, ghi lại host, port và phiên bản server. Mặc định local thường là `localhost:5432`; dùng giá trị thực trên máy bạn.
2. **Tạo database và hai role.** Tạo database `phone_advisor`, role `phone_admin` (owner/DDL/seed) và role `phone_app` (runtime web, chỉ đọc). Dùng mật khẩu local mạnh; role `postgres` chỉ dùng để khởi tạo, không chạy Flask. Mục đích là nếu có lỗi trong route/tool thì tài khoản web cũng không thể sửa/xóa catalog.
3. **Cài thư viện nền tảng** trong môi trường ảo: `SQLAlchemy`, `alembic`, `psycopg[binary]` và `python-dotenv`. Psycopg bản binary thuận tiện cho phát triển local; nếu môi trường sau này cần driver khác, đổi theo hướng dẫn triển khai.
4. **Tạo `.env` và `.env.example`.** Trong `.env` đặt `DATABASE_URL` cho role `phone_app` và `DATABASE_ADMIN_URL` cho role `phone_admin`, đều theo dạng `postgresql+psycopg://<user>:<mật_khẩu>@localhost:5432/phone_advisor`; thêm `.env` vào `.gitignore`. App dùng `DATABASE_URL`; Alembic và lệnh seed dùng `DATABASE_ADMIN_URL`. `.env.example` chỉ có giá trị mẫu, không có mật khẩu thật.
5. **Tạo module database** `src/phone_advisor/db/` gồm `base.py`, `models.py`, `session.py`. `base.py` cung cấp Declarative Base; `session.py` tạo engine và `sessionmaker` từ cấu hình, không tạo kết nối mới cho mỗi truy vấn.
6. **Khai báo bảng `products`.** Giữ `id` gốc CSV làm khóa chính, nhưng để database identity/sequence tạo ID cho sản phẩm mới sau này. Khai báo tên/hãng là chuỗi bắt buộc; `gia_ban` là số nguyên lớn theo VND; RAM, ROM, pin, sạc, Hz và camera là số nguyên nullable nếu dữ liệu thực tế cho phép thiếu; màn hình là số thập phân; chip, hệ điều hành và URL là chuỗi nullable. Có thể thêm `created_at`/`updated_at` để mô phỏng vòng đời bản ghi.
7. **Khai báo bảng tag quan hệ.** Tạo `tags` có `slug` duy nhất; tạo `product_tags` với khóa ngoại tới products/tags và khóa chính ghép. Không lưu danh sách tag như chuỗi phẩy trong cột `products`; chuẩn hóa quan hệ giúp lọc tag chính xác và ngăn tag mồ côi.
8. **Thêm ràng buộc và index vừa đủ.** Dùng khóa chính/khóa ngoại, unique cho tag slug và not-null cho trường bắt buộc. Có thể thêm index cho `hang` và `gia_ban` vì đây là bộ lọc thường dùng; chưa cần tối ưu phức tạp cho 162 sản phẩm.
9. **Khởi tạo Alembic.** Cấu hình Alembic nạp `DATABASE_ADMIN_URL` và metadata của models. Tạo migration đầu tiên bằng autogenerate, sau đó đọc file migration và sửa nếu cần; autogenerate có thể bỏ sót hoặc đoán sai một số thay đổi.
10. **Áp dụng migration** lên database local bằng role admin. Sau đó cấp cho role `phone_app` quyền connect, usage schema và SELECT trên ba bảng. Kiểm tra trong pgAdmin hoặc `psql` rằng có `products`, `tags`, `product_tags` và bảng version của Alembic; lúc này bảng dữ liệu sản phẩm có thể còn rỗng.
11. **Tạo quy tắc Session theo request.** Mở Session cho một đơn vị công việc/request, đóng sau khi xong; commit khi có ghi, rollback khi lỗi. Không giữ một SQLAlchemy Session dùng chung giữa các request hoặc luồng đồng thời.

Ví dụ cấp quyền đọc sau khi role/database đã được tạo (chạy trong database `phone_advisor` bằng role admin):

~~~sql
GRANT CONNECT ON DATABASE phone_advisor TO phone_app;
GRANT USAGE ON SCHEMA public TO phone_app;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO phone_app;
ALTER DEFAULT PRIVILEGES FOR ROLE phone_admin IN SCHEMA public
GRANT SELECT ON TABLES TO phone_app;
~~~

Nếu migration tạo bảng bằng role khác `phone_admin`, đổi role trong lệnh `ALTER DEFAULT PRIVILEGES` cho đúng chủ sở hữu bảng.

## Tệp cần tạo hoặc sửa

- `requirements.txt`
- `.env.example`, `.gitignore`
- `src/phone_advisor/config.py`
- `src/phone_advisor/db/base.py`, `models.py`, `session.py`
- `alembic.ini`, `migrations/`

## Tự kiểm tra

- Ứng dụng cấu hình đọc `DATABASE_URL` từ môi trường, không chứa mật khẩu trong source.
- Alembic upgrade chạy được trên database rỗng và tạo đủ ba bảng cùng các ràng buộc.
- Có thể xem schema qua pgAdmin/psql; bảng chưa bị seed dữ liệu ngoài ý muốn.
- Tắt/bật app không làm tạo schema hoặc nhập dữ liệu một cách âm thầm.

## Hoàn thành khi

Database và migration có thể dựng lại từ cấu hình/mã nguồn; models biểu diễn đúng sản phẩm và tag; bí mật local không nằm trong Git.

**Đầu ra cuối buổi:** PostgreSQL local có schema trống, sẵn sàng cho buổi import CSV.
