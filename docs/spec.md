# BẢN ĐẶC TẢ DỰ ÁN (SPECIFICATION): CHATBOT TƯ VẤN BÁN HÀNG ĐIỆN THOẠI

> **Tài liệu tham chiếu cốt lõi:** [`data/kientruc.md`](../data/kientruc.md)  
> **Lộ trình thực hiện:** [`docs/huong_dan_tung_buoi/`](huong_dan_tung_buoi/)  
> **Trạng thái:** Chờ xác nhận (Phase 1: SPECIFY)

---

## 1. Giả định ban đầu (Assumptions)

1. **Môi trường cục bộ (Local Environment):** Ứng dụng chạy trên máy cục bộ Windows với Python 3.10+, PostgreSQL local (`localhost:5432`) và Ollama local.
2. **Quy mô dữ liệu:** Sử dụng dữ liệu snapshot ban đầu từ `data/dien_thoai_chuan_hoa.csv` (162 sản phẩm). Sau bước seed, PostgreSQL là nguồn sự thật duy nhất (Single Source of Truth); runtime không đọc CSV.
3. **Phạm vi tính năng:**
   - Tư vấn, tìm kiếm, so sánh thông số, xem chi tiết điện thoại từ danh mục có sẵn.
   - **Không bao gồm:** Đặt hàng, thanh toán, quản lý giỏ hàng, cập nhật giá thời gian thực hoặc tra cứu bảo hành/kho hàng ngoài dữ liệu.
4. **Mô hình AI:** Sử dụng mô hình cục bộ qua Ollama (khuyến nghị dòng Qwen 2.5 như `qwen2.5:3b` hoặc `qwen2.5:7b` / Llama 3) phục vụ cho Agent reasoning và sinh văn bản tiếng Việt.

---

## 2. Mục tiêu dự án (Objective)

Xây dựng hệ thống Chatbot tư vấn điện thoại bằng tiếng Việt thông minh, minh bạch và an toàn:
- **Người dùng mục tiêu:** Khách hàng có nhu cầu tìm mua, khảo giá và so sánh các dòng điện thoại thông minh bằng ngôn ngữ tự nhiên.
- **Giá trị cốt lõi:** 
  - Khắc phục triệt để hiện tượng "ảo giác" (hallucination) của LLM bằng cơ chế **Deterministic Catalog Service + Tool Whitelist + Guardrails**.
  - Không bao giờ vi phạm điều kiện lọc cứng (giá, hãng, thông số).
  - Trích xuất chuẩn xác ngôn ngữ tiếng Việt (tiếng lóng, viết tắt, đơn vị tiền tệ "củ", "tr", "triệu").

---

## 3. Tech Stack

| Thành phần | Công nghệ / Thư viện | Vai trò |
|---|---|---|
| **Backend Framework** | FastAPI (ASGI), Uvicorn | Web API bất đồng bộ, routing, middleware, Swagger UI tự động |
| **Data Validation** | Pydantic v2 | Kiểm thực schema đầu vào API, tool schema contracts |
| **Database & ORM** | PostgreSQL, SQLModel (SQLAlchemy 2.0) | Lưu trữ quan hệ, truy vấn dữ liệu chuẩn xác |
| **Database Migrations** | Alembic | Quản lý phiên bản schema (`products`, `tags`, `product_tags`) |
| **Database Driver** | Psycopg 3 (`psycopg[binary]`) | Driver kết nối PostgreSQL hiệu năng cao |
| **NLP Pipeline** | SetFit (Sentence Transformers) | Phân loại 7 ý định (Few-shot learning trên CPU) |
| **Entity & Slot Matching** | RapidFuzz, Python `re`, `unicodedata` | Bóc tách hãng, model, khoảng giá, nhu cầu, chống lỗi gõ |
| **AI Agent** | Ollama API, Local LLM (Qwen 2.5 / Llama 3) | Điều phối hội thoại, gọi tool được cấp phép và diễn đạt kết quả |
| **Testing** | Pytest, HTTPX | Kiểm thử tự động từ unit test tới integration test |
| **Frontend** | HTML5, CSS3, JavaScript (Fetch API / SSE) | Giao diện chat trực quan, hiển thị Product Cards |

---

## 4. Lệnh thực thi tiêu chuẩn (Commands)

- **Thiết lập môi trường ảo:**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  ```
- **Quản lý Database Migration:**
  ```powershell
  alembic revision --autogenerate -m "init_schema"
  alembic upgrade head
  ```
- **Nạp dữ liệu ban đầu (Seed Catalog):**
  ```powershell
  python -m scripts.seed_catalog
  ```
- **Chạy ứng dụng (Development Server):**
  ```powershell
  uvicorn phone_advisor.app:app --reload --host 127.0.0.1 --port 8000
  ```
- **Chạy toàn bộ kiểm thử:**
  ```powershell
  pytest tests/ -v
  ```
- **Đánh giá chất lượng NLP:**
  ```powershell
  python evaluation/evaluate_nlp.py
  ```

---

## 5. Cấu trúc thư mục (Project Structure)

```text
E:\NLP/
├── data/
│   ├── dien_thoai_chuan_hoa.csv       # Dữ liệu seed gốc
│   ├── dien_thoai_chuan_hoa.json      # Dữ liệu tham chiếu
│   └── kientruc.md                    # Tài liệu kiến trúc chuẩn
├── docs/
│   ├── spec.md                        # Bản đặc tả dự án này
│   ├── mo_ta_du_lieu.md               # Data dictionary
│   └── huong_dan_tung_buoi/           # Chi tiết 14 buổi thực hiện
│       ├── README.md
│       ├── TIEN_DO.md
│       └── buoi_*.md
├── src/
│   └── phone_advisor/
│       ├── __init__.py
│       ├── app.py                     # Khởi tạo FastAPI app
│       ├── config.py                  # Quản lý settings & biến môi trường
│       ├── db/
│       │   ├── base.py
│       │   ├── models.py              # Models: Product, Tag, ProductTag
│       │   └── session.py             # Engine & Sessionmaker
│       ├── web/
│       │   ├── routes.py              # Endpoints: /api/chat, /health
│       │   ├── templates/             # Giao diện HTML
│       │   └── static/                # CSS, JS, hình ảnh
│       ├── nlp/
│       │   ├── normalize.py           # Chuẩn hóa Unicode, tiền tệ
│       │   ├── aliases.py             # Từ điển đồng nghĩa, tên model
│       │   ├── intent.py              # Phân loại intent bằng SetFit
│       │   ├── slots.py               # Bóc tách slot và validate
│       │   └── dialogue_state.py      # Lưu trữ ngữ cảnh hội thoại
│       ├── agent/
│       │   ├── orchestrator.py        # Điều phối Agent & Ollama client
│       │   ├── prompts/               # System prompt chống bịa đặt
│       │   ├── tool_schemas.py        # Pydantic schema cho 4 tools
│       │   └── tool_registry.py       # Whitelist và thực thi tool an toàn
│       └── catalog/
│           ├── repository.py          # Truy vấn PostgreSQL bằng SQLModel
│           ├── search.py              # Lọc sản phẩm theo điều kiện cứng
│           ├── recommend.py           # Xếp hạng sản phẩm theo sở thích
│           ├── browse.py              # Duyệt danh mục có phân trang
│           └── compare.py             # So sánh 2-3 sản phẩm
├── tests/
│   ├── test_nlp.py
│   ├── test_catalog.py
│   ├── test_agent_flow.py
│   └── fixtures/
├── evaluation/
│   ├── intent_slots.csv               # Tập dữ liệu mẫu đánh giá NLP
│   ├── evaluate_nlp.py                # Script tính Accuracy, F1
│   └── rubric_top3.md                 # Tiêu chuẩn chấm điểm gợi ý
├── migrations/                        # Alembic migrations
├── scripts/
│   ├── __init__.py
│   └── seed_catalog.py                # Script nạp dữ liệu từ CSV
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 6. Quy chuẩn Code (Code Style & Patterns)

- **Type Annotations & Validation:** 100% hàm nội bộ và contracts có type hints rõ ràng; sử dụng `Pydantic BaseModel` cho dữ liệu truyền nhận.
- **Repository Pattern:** Logic truy vấn SQL đóng gói hoàn toàn trong `src/phone_advisor/catalog/repository.py`, không viết raw SQL rải rác trong routes hay agent.
- **Tách bạch Hard Filters vs Preferences:**
  ```python
  # Ví dụ cấu trúc request chuẩn từ tầng NLP sang Catalog
  class QueryRequest(BaseModel):
      intent: str  # recommend, search, detail, compare, browse, greeting, out_of_scope
      filters: ProductFilters  # Bắt buộc khớp 100% (hãng, khoảng giá, min ram...)
      preferences: list[PreferenceItem] = []  # Chỉ dùng để tính điểm ranking
      excluded_brands: list[str] = []
      excluded_product_ids: list[int] = []
      limit: int = 3
  ```
- **Quản lý Session Database:** Mỗi request HTTP mở 1 session riêng biệt, xử lý xong phải đóng (qua FastAPI `Depends(get_session)`).

---

## 7. Chiến lược kiểm thử (Testing Strategy)

1. **Tầng Catalog & Database (Unit/Integration Test):**
   - Kiểm tra lọc chính xác theo toán tử: `<`, `<=`, `>`, `>=`, `=`, `IN`.
   - Kiểm tra tính toán tử bao gồm biên: "dưới 15 triệu" loại 15tr; "tối đa 15 triệu" lấy cả 15tr.
   - Kiểm tra logic xếp hạng: ưu tiên pin xếp theo `pin_mah` giảm dần; máy không có tag sở thích không bị loại trừ nếu thỏa điều kiện cứng.
2. **Tầng NLP:**
   - Kiểm tra chuẩn hóa tiền tệ ("15 củ" $\rightarrow$ 15.000.000, "15tr" $\rightarrow$ 15.000.000).
   - Kiểm tra 7 intents trên tập test `evaluation/intent_slots.csv`.
   - Kiểm tra trích xuất slot phủ định ("không lấy Samsung" $\rightarrow$ `excluded_brands: ["Samsung"]`).
3. **Tầng Agent & Tool Guardrails:**
   - Chặn đứng mọi lời gọi tool ngoài whitelist 4 tool cho phép.
   - Đảm bảo khi Ollama bị ngắt kết nối (offline), hệ thống tự động kích hoạt fallback trả kết quả từ Catalog.
4. **Tầng API & UI:**
   - Kiểm tra CSRF, Session Cookie isolation giữa các phiên chat khác nhau.
   - Escape toàn bộ chuỗi HTML để chống XSS.

---

## 8. Giới hạn và Nguyên tắc bất khả xâm phạm (Boundaries)

### Luôn luôn làm (Always):
- Chạy unit test sau mỗi module hoàn thiện.
- Sử dụng Pydantic để kiểm thực đầu vào API và tham số tool.
- Quản lý phiên hội thoại độc lập theo session ID ngẫu nhiên trên server.
- Trả lời và diễn đạt bằng Tiếng Việt tự nhiên, thân thiện.

### Phải hỏi trước (Ask First):
- Thay đổi schema database hoặc thay đổi cấu trúc bảng `dien_thoai_chuan_hoa.csv`.
- Thêm thư viện nặng vào `requirements.txt`.
- Sửa đổi cơ chế ranking sản phẩm cốt lõi.

### Tuyệt đối không làm (Never):
- **Không bao giờ xóa database** khi chưa có sự đồng ý tường minh của người dùng.
- **Không bao giờ cho phép LLM tự bịa đặt** giá cả, thông số cấu hình, tồn kho hoặc chính sách khuyến mãi ngoài database.
- **Không cấp quyền ghi (INSERT/UPDATE/DELETE)** cho Agent; Agent chỉ có quyền đọc (Read-only).
- **Không hardcode thông tin nhạy cảm** (mật khẩu DB, secret keys) vào Git repository.

---

## 9. Tiêu chí hoàn thành (Success Criteria)

- [ ] **Tỷ lệ vi phạm điều kiện cứng:** 0% (Không bao giờ trả sản phẩm vượt giá ngân sách hoặc sai hãng bắt buộc).
- [ ] **Độ chính xác NLP:** Intent Classification Accuracy $\ge 85\%$; Slot Extraction F1-score $\ge 80\%$.
- [ ] **Tính ổn định (Resilience):** Hệ thống vẫn trả kết quả danh mục dạng thẻ khi Ollama offline nhờ cơ chế Template Fallback.
- [ ] **Khả năng giải thích:** Mỗi gợi ý gửi về đều có kèm lý do cụ thể dựa trên thông số hoặc tag trong database.
- [ ] **Bảo mật:** Không có lỗ hổng XSS trên UI; session của 2 người dùng khác nhau hoàn toàn cô lập.

---

## 10. Kế hoạch triển khai đề xuất (Next Steps)

Theo lộ trình 14 buổi tại [`docs/huong_dan_tung_buoi/`](huong_dan_tung_buoi/):
- **Giai đoạn tiếp theo (Phase 2 & 3):** Lập kế hoạch chi tiết cho **Buổi 1 (Môi trường & Khung dự án)** và **Buổi 2 (Kiểm tra dữ liệu CSV)**, phân chia task cụ thể để bắt tay vào thực hiện bằng phương pháp TDD.

