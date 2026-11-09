"""
Script đánh giá định lượng chất lượng NLP và Mô hình cho Chatbot Tư vấn Điện thoại.
Đo lường:
1. Intent Classification Accuracy
2. Slot Extraction Precision, Recall, F1-Score (Hãng, Giá, Tag bắt buộc, Sở thích, Phủ định)
3. Hard Constraints Compliance Rate (Tỷ lệ tuân thủ điều kiện cứng - Bắt buộc 100%)
4. Clarification Detection Accuracy (Phát hiện câu mâu thuẫn/cần hỏi lại)
"""

import csv
import json
import os
import sys
from typing import Dict, Any, List, Tuple


def calculate_metrics(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    """Tính Precision, Recall, F1-Score."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


class BaselineDummyParser:
    """
    Parser mẫu cơ bản dùng regex/từ khóa để chạy thử nghiệm khi chưa kết nối module NLP chính.
    Khi bạn đã viết xong `src/phone_advisor/nlp`, bạn có thể thay thế class này bằng parser thực tế.
    """
    def __init__(self):
        self.brands = ["Apple", "Samsung", "OPPO", "Xiaomi", "vivo", "realme", "HONOR", "Tecno", "Motorola", "Nothing Phone", "Nubia"]
        self.brand_aliases = {
            "ip": "Apple",
            "iphone": "Apple",
            "sámung": "Samsung",
            "ss": "Samsung",
        }

    def parse(self, text: str) -> Dict[str, Any]:
        lower_text = text.lower()
        
        # Mâu thuẫn giá
        if "dưới 5 triệu" in lower_text and "trên 10 triệu" in lower_text:
            return {"needs_clarification": True}

        # Intent cơ bản
        if any(w in lower_text for w in ["laptop", "thời tiết", "nhân viên", "macbook", "bảo hành bao lâu"]):
            intent = "out_of_scope"
        elif any(w in lower_text for w in ["chào", "hello", "hi"]):
            intent = "greeting"
        elif "so sánh" in lower_text:
            intent = "compare"
        elif "chi tiết" in lower_text or "thông số" in lower_text:
            intent = "detail"
        elif "liệt kê" in lower_text or "danh mục" in lower_text or "tất cả" in lower_text:
            intent = "browse"
        elif "có máy nào" in lower_text or "máy nào" in lower_text or "tìm máy" in lower_text:
            intent = "search"
        else:
            intent = "recommend"

        # Trích xuất hãng
        detected_brand = None
        for b in self.brands:
            if b.lower() in lower_text:
                detected_brand = b
                break
        if not detected_brand:
            for alias, target in self.brand_aliases.items():
                if f" {alias} " in f" {lower_text} ":
                    detected_brand = target
                    break

        # Phủ định / Exclusions
        exclusions = None
        if "không lấy apple" in lower_text or "trừ apple" in lower_text:
            exclusions = "Apple"
        elif "trừ samsung" in lower_text:
            exclusions = "Samsung"
        elif "không lấy máy gập" in lower_text:
            exclusions = "thiet_ke_gap"

        return {
            "intent": intent,
            "brand": detected_brand,
            "price_min": None,
            "price_max": None,
            "required_tags": None,
            "preferences": None,
            "exclusions": exclusions,
            "needs_clarification": False
        }


def evaluate(test_file: str, parser=None) -> Dict[str, Any]:
    if parser is None:
        parser = BaselineDummyParser()

    if not os.path.exists(test_file):
        raise FileNotFoundError(f"Không tìm thấy file test: {test_file}")

    total_cases = 0
    intent_correct = 0
    clarification_correct = 0
    hard_violations = 0

    brand_tp, brand_fp, brand_fn = 0, 0, 0
    exclusion_tp, exclusion_fp, exclusion_fn = 0, 0, 0
    
    failures = []

    with open(test_file, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_cases += 1
            cid = row["id"]
            text = row["text"]
            exp_intent = row["expected_intent"].strip()
            exp_brand = row["expected_brand"].strip() or None
            exp_exclusions = row["expected_exclusions"].strip() or None
            exp_clarify = row["needs_clarification"].strip().lower() == "true"

            # Chạy dự đoán
            pred = parser.parse(text)

            # 1. Đánh giá Clarification
            pred_clarify = pred.get("needs_clarification", False)
            if pred_clarify == exp_clarify:
                clarification_correct += 1
            elif exp_clarify:
                failures.append({
                    "id": cid, "text": text,
                    "error_type": "Missed Clarification",
                    "expected": "Needs clarification",
                    "predicted": "Processed normally"
                })

            # Nếu là case mâu thuẫn cần hỏi lại, không chấm tiếp intent/slot
            if exp_clarify:
                continue

            # 2. Đánh giá Intent
            pred_intent = pred.get("intent")
            if pred_intent == exp_intent:
                intent_correct += 1
            else:
                failures.append({
                    "id": cid, "text": text,
                    "error_type": "Wrong Intent",
                    "expected": exp_intent,
                    "predicted": pred_intent
                })

            # 3. Đánh giá Slot Hãng (Brand)
            pred_brand = pred.get("brand")
            if exp_brand and pred_brand == exp_brand:
                brand_tp += 1
            elif exp_brand and pred_brand != exp_brand:
                brand_fn += 1
                failures.append({
                    "id": cid, "text": text,
                    "error_type": "Wrong Brand",
                    "expected": exp_brand,
                    "predicted": pred_brand
                })
            elif not exp_brand and pred_brand:
                brand_fp += 1

            # 4. Đánh giá Phủ định / Loại trừ (Exclusion)
            pred_excl = pred.get("exclusions")
            if exp_exclusions and pred_excl == exp_exclusions:
                exclusion_tp += 1
            elif exp_exclusions and pred_excl != exp_exclusions:
                exclusion_fn += 1
                hard_violations += 1  # Bỏ sót điều kiện loại trừ được tính là vi phạm điều kiện cứng
                failures.append({
                    "id": cid, "text": text,
                    "error_type": "Hard Violation (Missed Exclusion)",
                    "expected": exp_exclusions,
                    "predicted": pred_excl
                })
            elif not exp_exclusions and pred_excl:
                exclusion_fp += 1

    # Tính toán chỉ số
    intent_acc = (intent_correct / (total_cases - 1)) if total_cases > 1 else 0.0
    clarify_acc = clarification_correct / total_cases if total_cases > 0 else 0.0
    brand_p, brand_r, brand_f1 = calculate_metrics(brand_tp, brand_fp, brand_fn)
    excl_p, excl_r, excl_f1 = calculate_metrics(exclusion_tp, exclusion_fp, exclusion_fn)

    hard_compliance_rate = ((total_cases - hard_violations) / total_cases) * 100.0

    report = {
        "total_cases": total_cases,
        "intent_accuracy": round(intent_acc * 100, 2),
        "clarification_accuracy": round(clarify_acc * 100, 2),
        "hard_constraint_compliance_rate": round(hard_compliance_rate, 2),
        "slots": {
            "brand": {"precision": round(brand_p * 100, 2), "recall": round(brand_r * 100, 2), "f1": round(brand_f1 * 100, 2)},
            "exclusion": {"precision": round(excl_p * 100, 2), "recall": round(excl_r * 100, 2), "f1": round(excl_f1 * 100, 2)},
        },
        "total_failures": len(failures),
        "failures_sample": failures[:10]
    }
    return report


def print_report(report: Dict[str, Any]):
    print("=" * 65)
    print("        BÁO CÁO KẾT QUẢ ĐÁNH GIÁ CHẤT LƯỢNG NLP & MÔ HÌNH")
    print("=" * 65)
    print(f"Tổng số tình huống kiểm thử (Test cases): {report['total_cases']}")
    print("-" * 65)
    print(f"1. Độ chính xác Ý định (Intent Accuracy):        {report['intent_accuracy']}%")
    print(f"2. Phát hiện câu mâu thuẫn/hỏi lại (Clarify):   {report['clarification_accuracy']}%")
    print(f"3. Tuân thủ điều kiện cứng (Hard Constraints):  {report['hard_constraint_compliance_rate']}% (Mục tiêu: 100%)")
    print("-" * 65)
    print("4. Độ chính xác trích xuất thực thể (Slot F1-Scores):")
    for slot_name, metrics in report["slots"].items():
        print(f"   - {slot_name.upper():<12}: Precision: {metrics['precision']}% | Recall: {metrics['recall']}% | F1: {metrics['f1']}%")
    print("-" * 65)
    print(f"Tổng số ca chưa đạt: {report['total_failures']}")
    if report["failures_sample"]:
        print("\nCác ca lỗi tiêu biểu để tối ưu:")
        for idx, f in enumerate(report["failures_sample"], 1):
            print(f"  [{idx}] Câu: \"{f['text']}\"")
            print(f"      Lỗi: {f['error_type']} | Kỳ vọng: {f['expected']} | Dự đoán: {f['predicted']}")
    print("=" * 65)


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_csv = os.path.join(current_dir, "intent_slots.csv")
    print(f"Đang chạy đánh giá trên file: {test_csv}\n")
    results = evaluate(test_csv)
    print_report(results)

