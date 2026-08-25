# Tóm Tắt Hệ Thống Thực Nghiệm (Experiment Summary - Model_final_v3)

---

## 1. Dữ Liệu & Phân Chia (Master Stratified Split)

* **Tập dữ liệu chuẩn vàng:** `data/gold_standard_final_48670.csv` ($N = 48,670$ bình luận).
* **Phân tầng:** `Train: 38,936 (80%)` | `Dev: 4,867 (10%)` | `Test: 4,867 (10% - LOCKED)`.
* **Tác vụ 1 (Toxicity):** `NON-TOXIC` (42,810 mẫu - 87.96%) vs `TOXIC` (5,860 mẫu - 12.04%).
* **Tác vụ 2 (Expression - Trên tập TOXIC):** `EXPLICIT` (4,999 mẫu - 85.31%) vs `IMPLICIT` (861 mẫu - 14.69%).

---

## 2. Thiết Kế Huấn Luyện Chuẩn Hóa

* **Độ dài Token (`max_length`):** Cố định `128` (Độ phủ $>98.11\%$ trên tất cả các tokenizer theo phân tích thực tế).
* **Trọng số hàm mất mát (Class Weights):** Tính toán **nghiêm ngặt chỉ từ tập Train**.
* **Cơ chế Early Stopping:** Theo dõi **Dev Macro-F1** với `patience = 3` (Transformer) / `patience = 4` (TextCNN).
* **Gradient Accumulation:** `Physical Batch Size = 16`, `Gradient Accumulation Steps = 2` $\rightarrow$ `Effective Batch Size = 32`.
* **Khóa tập Test:** Khôi phục `best_model` được chọn từ Dev để đánh giá Test đúng 1 lần duy nhất.

---

## 3. Bảng Tổng Hợp Kết Quả Thực Nghiệm (Locked Test Set)

### Tác vụ 1: Phân loại TOXIC / NON-TOXIC

| Mô hình | Kiến trúc | Accuracy | Macro Precision | Macro Recall | Macro F1 | Weighted F1 | PR-AUC (TOXIC) | Trạng thái |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **TextCNN** | 1D-CNN (Word Embeddings) | **0.8956** | 0.7544 | 0.7308 | **0.7417** | 0.8931 | 0.5782 | **COMPLETED** |
| **PhoBERT** | RoBERTa-base (Monolingual) | **0.9176** | 0.8129 | 0.7786 | **0.7943** | 0.9152 | 0.6943 | **COMPLETED** |
| **ViDeBERTa** | DeBERTa-base (Disentangled) | **0.7658** | 0.5530 | 0.5782 | **0.5575** | 0.7880 | 0.1888 | **COMPLETED** |
| **XLM-R** | RoBERTa-base (Multilingual) | **0.9088** | 0.7841 | 0.7891 | **0.7865** | 0.9092 | 0.6819 | **COMPLETED** |

### Tác vụ 2: Phân loại EXPLICIT / IMPLICIT

| Mô hình | Kiến trúc | Accuracy | Macro Precision | Macro Recall | Macro F1 | Weighted F1 | PR-AUC (IMPLICIT) | Trạng thái |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **TextCNN** | 1D-CNN (Word Embeddings) | **0.7150** | 0.6004 | 0.6741 | **0.6013** | 0.7517 | 0.3502 | **COMPLETED** |
| **PhoBERT** | RoBERTa-base (Monolingual) | **0.8003** | 0.6513 | 0.7097 | **0.6692** | 0.8163 | 0.5016 | **COMPLETED** |
| **ViDeBERTa** | DeBERTa-base (Disentangled) | **0.8106** | 0.5409 | 0.5231 | **0.5230** | 0.7847 | 0.2274 | **COMPLETED** |
| **XLM-R** | RoBERTa-base (Multilingual) | **0.8379** | 0.6865 | 0.7124 | **0.6978** | 0.8432 | 0.4628 | **COMPLETED** |

---

## 4. Danh Mục Hiện Vật Đã Hoàn Thành (Artifacts Checklist)

- [x] `data/gold_standard_final_48670.csv` (Đã kiểm định 100%)
- [x] `data_splits/` (`train.csv`, `dev.csv`, `test.csv`, `split_manifest.csv`, `split_metadata.json`)
- [x] `results/token_length_analysis.csv` (Đo đạc thực tế trên tập Train)
- [x] `results/test_results_task1.csv` & `test_results_task2.csv` (Hoàn chỉnh 4 mô hình)
- [x] `results/per_class_metrics.csv` (Đầy đủ precision, recall, F1 cho 4 mô hình x 2 tác vụ)
- [x] `results/predictions/` (Đầy đủ file dự đoán của cả 4 mô hình x 2 tác vụ)
- [x] `results/confusion_matrices/` (Đầy đủ 8 ma trận nhầm lẫn của 4 mô hình x 2 tác vụ)
- [x] `results/length_analysis.csv` & `results/error_cases.csv` (Phân tích lỗi & độ dài hoàn chỉnh)
- [x] `artifacts/` (`phobert/`, `textcnn/`, `videberta/`, `xlmr/` với đầy đủ lịch sử huấn luyện & metrics)
- [x] `figures/` (8 biểu đồ so sánh, ma trận nhầm lẫn, phân tích độ dài & learning curve)
- [x] `notebooks/` (`00_Prepare_Data.ipynb` đến `05_Aggregate_Results.ipynb` + Colab Pipeline)
- [x] `report/report_metrics.json` & `report/chuong_4_thuc_nghiem_va_phan_tich_ket_qua.md`
