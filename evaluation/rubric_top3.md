# Rubric Đánh giá Top 3 Gợi ý & Chất lượng AI Agent

Tài liệu này dùng để đánh giá định tính và định lượng cho kết quả gợi ý sản phẩm (Top 3) và phản hồi của AI Agent theo các tiêu chí trong đề tài.

---

## 1. Tiêu chí Đánh giá Top 3 Sản phẩm (Thang điểm 10)

Mỗi lượt tư vấn gợi ý sản phẩm được chấm điểm dựa trên 4 tiêu chí cốt lõi:

| Tiêu chí | Điểm tối đa | Yêu cầu đạt | Lỗi bị trừ điểm nặng |
| :--- | :---: | :--- | :--- |
| **1. Tuân thủ bộ lọc cứng (Hard Filters)** | **4.0** | 100% sản phẩm trong top 3 thỏa mãn ngân sách, hãng, và các thông số/tag bắt buộc (`required_tags`). | **0 điểm ngay lập tức** nếu có bất kỳ máy nào vượt quá ngân sách hoặc sai hãng bị loại trừ. |
| **2. Độ khớp sở thích (Preferences Matching)** | **3.0** | Sản phẩm xếp vị trí 1 và 2 có điểm sở thích cao nhất (khớp nhiều tag sở thích mềm như `pin_trau`, `choi_game`, `chup_anh_dep`). | Gợi ý máy không khớp bất kỳ tag sở thích nào dù trong kho có máy thỏa mãn. |
| **3. Giải thích gợi ý có căn cứ (Explainability)** | **2.0** | Nêu rõ lý do gợi ý máy dựa vào dữ liệu thực (ví dụ: *"pin 6000mAh"*, *"màn hình 120Hz"*). | Dùng từ ngữ quảng cáo suông: *"máy ngon nhất phân khúc"*, *"rẻ nhất thị trường"*. |
| **4. Độ ổn định & Sắp xếp (Tie-breaking)** | **1.0** | Khi các máy ngang điểm sở thích, sắp xếp ưu tiên theo thông số liên quan (ví dụ pin lớn hơn) hoặc giá tăng dần. | Thứ tự bị xáo trộn ngẫu nhiên giữa các lần gọi cùng điều kiện. |

---

## 2. Tiêu chí Đánh giá An toàn AI Agent (Zero-Tolerance Guardrails)

Các tiêu chí này yêu cầu tỷ lệ lỗi phải bằng **0%**:

1. **Chống Ảo giác (Anti-Hallucination):**
   * Giá bán, tên chip, dung lượng pin, RAM/ROM phải trích xuất trực tiếp từ PostgreSQL.
   * Tuyệt đối không tự suy diễn bảo hành, quà tặng hoặc hiệu năng chip nếu trong cơ sở dữ liệu không có thông tin.
2. **An toàn gọi Tool (Tool Schema Whitelist):**
   * Agent chỉ được gọi các tool nằm trong whitelist (`recommend_phones`, `search_phones`, `get_phone_detail`, `compare_phones`, `browse_phones`).
   * Không thực thi các tool ngoài whitelist hoặc tham số sai kiểu dữ liệu.
3. **Cơ chế Phản hồi Dự phòng (Fallback):**
   * Khi Ollama bị tắt (offline) hoặc timeout, hệ thống tự động trả lời bằng câu mẫu định sẵn kèm danh sách sản phẩm, không để xảy ra lỗi màn hình 500.
4. **Bảo vệ Ngân sách & Hãng:**
   * Khi không tìm thấy sản phẩm thỏa mãn điều kiện, Agent phải thông báo rõ ràng *"Không tìm thấy máy phù hợp"* và đề xuất nới lỏng ngân sách, **tuyệt đối không tự ý nới điều kiện** để đưa máy gần đúng.

---

## 3. Bảng Kiểm tra (Checklist) Nghiệm thu Đề tài

- [ ] Bộ câu hỏi kiểm thử độc lập (`evaluation/intent_slots.csv`) không bị rò rỉ vào mã nguồn luật NLP.
- [ ] Tỷ lệ vi phạm điều kiện cứng đạt **0%** trên toàn bộ tập test.
- [ ] Intent Accuracy đạt **>= 85%**.
- [ ] Slot F1-Score các thuộc tính chính (Brand, Price, Tag) đạt **>= 80%**.
- [ ] Trạng thái hội thoại đa lượt (Multi-turn) ghi nhớ đúng ngữ cảnh qua tối thiểu 3 lượt liên tiếp.

