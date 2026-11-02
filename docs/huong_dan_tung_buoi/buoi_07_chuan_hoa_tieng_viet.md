# Buổi 7 — Chuẩn hóa tiếng Việt, giá và alias

**Thời lượng gợi ý:** 2–3 giờ  
**Phụ thuộc:** Buổi 6  
**Đọc trước:** [`kientruc.md`](../../data/kientruc.md), mục 4.2 A, C, D và D½

## Mục tiêu

Chuẩn hóa cách viết để “15 củ”, “15tr” và “15 triệu” cùng thành 15.000.000 VND; chuẩn hóa hãng, tag và tên model mà vẫn giữ nguyên câu gốc.

## Vì sao chưa dùng LLM?

Các biến thể phổ biến có thể xử lý bằng luật và bảng alias nhỏ. Làm phần này trước giúp biết parser sai ở đâu, rẻ hơn và dễ giải thích hơn việc đưa mọi câu hỏi cho model.

## Các bước

1. **Tạo `nlp/normalize.py`.** Lưu nguyên câu người dùng; tạo bản so khớp riêng bằng chuẩn hóa Unicode NFC, chữ thường, khoảng trắng và dấu câu.
2. **Viết parser tiền có ví dụ được kiểm tra:** số nguyên/thập phân với `tr`, `triệu`, `củ`; chuyển về VND. Không đoán ngân sách từ “giá sinh viên”, “tầm trung” hoặc “flagship”.
3. **Bảo toàn toán tử giá:** trả giá trị kèm inclusive/exclusive. Ví dụ `< 15.000.000` khác `<= 15.000.000`.
4. **Tạo `nlp/aliases.py`.** Chuẩn hóa tên hãng và từ đồng nghĩa sang tag có trong CSV. Nhóm từ thay thế như `pin_trau`/`pin_khung` giữ quan hệ OR, không tạo hai điều kiện AND.
5. **Làm bảng alias model** từ tên thật trong CSV. Nếu alias khớp đúng một sản phẩm thì trả ID; nếu nhiều model/ROM thì trả danh sách lựa chọn; không tự đoán.
6. **Xử lý phủ định có ngữ cảnh.** “Không lấy máy gập” là loại tag; “không cần máy gập” chỉ nói không cần ưu tiên, không tự loại máy gập.
7. **Viết kiểm tra cho các cặp dễ nhầm:** 15tr/15 triệu, “dưới”/“tối đa”, “trên”/“ít nhất”, phủ định, tên không dấu và tên model trùng.

## Tệp cần tạo hoặc sửa

- `src/phone_advisor/nlp/normalize.py`
- `src/phone_advisor/nlp/aliases.py`
- `tests/test_nlp.py`
- `docs/mo_ta_du_lieu.md` nếu alias phụ thuộc cách ghi tên trong CSV

## Tự kiểm tra

- Câu gốc còn nguyên và không dùng bản không dấu làm câu trả lời.
- Parser giá không làm tròn sai; đơn vị đều ra VND.
- Mỗi tag đầu ra nằm trong tập tag của CSV.
- Alias trùng không trả ID giả định; parser báo nhiều lựa chọn.
- Cụm từ chủ quan không tự biến thành giới hạn giá cứng.

## Hoàn thành khi

Normalization và alias hoạt động độc lập, có kiểm tra cho ranh giới giá và các trường hợp mơ hồ.

**Đầu ra cuối buổi:** lớp chuẩn hóa ngôn ngữ không phụ thuộc Ollama.


