# Thư mục Đánh giá & Kiểm thử Hệ thống (Evaluation)

Thư mục này chứa toàn bộ tài nguyên, dữ liệu và công cụ để đánh giá định lượng và định tính cho đề tài **Chatbot Tư vấn Điện thoại Thông minh** theo yêu cầu của Buổi 14 và tiêu chuẩn nghiệm thu.

---

## 1. Cấu trúc thư mục

* [`intent_slots.csv`](file:///E:/NLP/evaluation/intent_slots.csv): Bộ dữ liệu kiểm thử độc lập gồm 50 tình huống câu nói tự nhiên tiếng Việt đã được gán nhãn chuẩn (Ground Truth).
* [`evaluate_nlp.py`](file:///E:/NLP/evaluation/evaluate_nlp.py): Script Python tự động chạy kiểm thử, tính toán Accuracy, Precision, Recall, F1 và Tỷ lệ vi phạm điều kiện cứng.
* [`rubric_top3.md`](file:///E:/NLP/evaluation/rubric_top3.md): Tiêu chuẩn chấm điểm chất lượng gợi ý Top 3 sản phẩm và an toàn AI Agent (Anti-hallucination, Fallback).

---

## 2. Mô tả các nhóm dữ liệu trong `intent_slots.csv`

Tập dữ liệu 50 câu kiểm thử bao quát các tình huống thực tế của người dùng Việt Nam:
1. **Normal:** Câu chuẩn ngữ pháp, có dấu, đầy đủ thông tin.
2. **Slang:** Tiếng lóng tiền tệ (*"củ"*, *"tr"*, *"chai"*, *"lốp"*), nhu cầu (*"pin trâu"*, *"chơi game mượt"*).
3. **No-accent:** Tiếng Việt không dấu (*"tim xiaomi duoi 8tr choi game"*).
4. **Boundary:** Kiểm tra toán tử biên (*"dưới 15 triệu"* `<` vs *"tối đa 15 triệu"* `<=`).
5. **Negation:** Phủ định và loại trừ (*"không lấy Apple"*, *"trừ máy gập"*).
6. **Conflict / Clarification:** Câu mâu thuẫn điều kiện giá cần bot kích hoạt hỏi lại (*"dưới 5 triệu nhưng trên 10 triệu"*).
7. **Out-of-scope / Greeting:** Các câu chào hỏi hoặc hỏi ngoài phạm vi nghiệp vụ (*"shop có bán laptop không"*).

---

## 3. Hướng dẫn chạy đánh giá

Từ thư mục gốc dự án (`E:\NLP`), chạy lệnh sau trong terminal:

```bash
python evaluation/evaluate_nlp.py
```

Kết quả hiển thị trên terminal gồm:
* **Intent Accuracy:** Tỷ lệ phân loại đúng ý định người dùng.
* **Clarification Accuracy:** Tỷ lệ phát hiện đúng câu mâu thuẫn cần hỏi lại.
* **Hard Constraint Compliance Rate:** Tỷ lệ tuân thủ điều kiện cứng (Yêu cầu nghiêm ngặt: 100%).
* **Slot F1-Scores:** Precision, Recall, F1 của từng thực thể (Brand, Price, Tag, Exclusion).
* **Error Analysis:** Danh sách các ca dự đoán sai và nguyên nhân để tinh chỉnh module NLP.

---

## 4. Cách tích hợp Module NLP thực tế vào Script đánh giá

Khi hoàn thành **Buổi 7 & Buổi 8** (viết xong `src/phone_advisor/nlp`), bạn chỉ cần mở file [`evaluate_nlp.py`](file:///E:/NLP/evaluation/evaluate_nlp.py) và thay thế `BaselineDummyParser` bằng parser thực tế:

```python
# Thay vì dùng DummyParser:
# parser = BaselineDummyParser()

# Nhập parser thực tế của dự án:
from phone_advisor.nlp.parser import PhoneNLPParser
parser = PhoneNLPParser()
```

