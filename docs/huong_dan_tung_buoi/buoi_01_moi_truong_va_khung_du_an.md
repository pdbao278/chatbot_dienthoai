# Buổi 1 — Chuẩn bị môi trường và khung dự án

**Thời lượng gợi ý:** 1,5–2 giờ  
**Phụ thuộc:** Không có  
**Đọc trước:** [`kientruc.md`](../../data/kientruc.md), mục 3, 9 và 10

## Mục tiêu

Tạo môi trường Python riêng, dựng cấu trúc module ban đầu và chạy được Flask với một route kiểm tra sức khỏe. Chưa đọc CSV, chưa viết NLP và chưa kết nối Ollama.

## Vì sao làm buổi này trước?

Môi trường riêng giúp tránh xung đột thư viện với các dự án khác. Route tối thiểu xác nhận Python/Flask chạy trước khi thêm catalog; nếu có lỗi cấu hình, ta biết nó nằm ở nền tảng chứ chưa bị trộn với logic sản phẩm.

## Các bước

1. **Kiểm tra workspace.** Xác nhận đang ở `E:\NLP`, các file dữ liệu hiện có trong `data/` và chưa chuyển/đổi tên CSV.
2. **Tạo virtual environment.** Trong PowerShell chạy `py -m venv .venv`, sau đó kích hoạt bằng `.\.venv\Scripts\Activate.ps1`. Nếu lệnh `py` không có, dùng `python -m venv .venv`.
3. **Tạo `requirements.txt` nền.** Bắt đầu với Flask, SQLAlchemy, Alembic, `psycopg[binary]`, `python-dotenv` và pandas (chỉ để kiểm tra dữ liệu nếu cần). Chạy `python -m pip install -r requirements.txt`. Chưa thêm thư viện Ollama hoặc NLP nâng cao cho đến khi cần ở các buổi sau.
4. **Tạo cấu trúc thư mục** theo mục 3 của kiến trúc: `src/phone_advisor/db/`, `web/`, `nlp/`, `agent/`, `catalog/`, `scripts/`, `migrations/`, `tests/` và `data/`. Thêm `__init__.py` cho package Python phù hợp.
5. **Tạo `.gitignore`.** Bỏ qua `.venv/`, `__pycache__/`, `.pytest_cache/`, file `.env` và dữ liệu sinh trong lúc chạy.
6. **Tạo Flask app tối thiểu** ở `src/phone_advisor/app.py`, thêm route `GET /health` trả JSON `{ "status": "ok" }` và khối `if __name__ == "__main__":` để chạy development server chỉ trên `127.0.0.1`.
7. **Chạy ứng dụng và kiểm tra route.** Từ root chạy `Set-Location .\src`, rồi `python -m phone_advisor.app`. Trong terminal khác gọi `Invoke-RestMethod http://127.0.0.1:5000/health`; sau đó dừng server bình thường.

## Tệp cần tạo hoặc sửa

- `requirements.txt`
- `.gitignore`
- `src/phone_advisor/__init__.py`
- `src/phone_advisor/app.py`
- Các thư mục module ban đầu

## Tự kiểm tra

- `python --version` và `python -m pip list` chạy trong `.venv`.
- Flask khởi động, `/health` trả đúng JSON; route health chưa tự seed hoặc phụ thuộc vào CSV.
- Đóng terminal hoặc thoát environment rồi kích hoạt lại vẫn chạy được.
- Không có file `.env`, khóa bí mật hay `.venv/` bị đưa vào Git.

## Hoàn thành khi

- Có thể dựng lại môi trường từ `requirements.txt`.
- Flask chạy được mà chưa cần đọc dữ liệu hoặc gọi Ollama.
- Tên thư mục/package thống nhất với kiến trúc.

**Đầu ra cuối buổi:** khung dự án chạy được và danh sách thư viện ban đầu.

