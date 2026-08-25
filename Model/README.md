# Nhận diện và Phân loại Phát ngôn Độc hại trên Mạng Xã hội Tiếng Việt (DS108 - Model_final_v3)

Dự án nghiên cứu xây dựng và thực nghiệm hệ thống phân loại phân cấp 2 tầng (*Hierarchical 2-stage Toxic Language Detection*) trên bộ dữ liệu chuẩn vàng gồm **48,670 bình luận mạng xã hội tiếng Việt**.

---

## 📌 Tổng quan Cấu trúc Phân loại

1. **Tác vụ 1 (Toxicity Classification):** Phân loại nhị phân `NON-TOXIC` (42,810 mẫu - 87.96%) vs `TOXIC` (5,860 mẫu - 12.04%).
2. **Tác vụ 2 (Expression Type Classification):** Phân loại trên tập con `TOXIC` thành `EXPLICIT` (4,999 mẫu - 85.31%) vs `IMPLICIT` (861 mẫu - 14.69%).

---

## 🏗️ 4 Mô hình Thực nghiệm

| STT | Mô hình | Loại kiến trúc | Checkpoint / Framework | Tiền xử lý |
| :---: | :--- | :--- | :--- | :--- |
| 1 | **TextCNN** | 1D-CNN Baseline | PyTorch (Filter sizes 2, 3, 4, 5) | Whitespace + Vocab tập Train |
| 2 | **PhoBERT** | Transformer Đơn ngữ | `vinai/phobert-base-v2` | Tách từ PyVi (`ViTokenizer`) + BPE |
| 3 | **ViDeBERTa** | Disentangled Attention | `Fsoft-AIC/videberta-base` | BPE Subword |
| 4 | **XLM-R** | Transformer Đa ngôn ngữ | `FacebookAI/xlm-roberta-base` | SentencePiece (250K subwords) |

---

## 📁 Cấu trúc Thư mục Dự án

```text
Model_final_v3/
├── README.md                                          # Tài liệu hướng dẫn sử dụng chi tiết
├── requirements.txt                                   # Danh mục thư viện phụ thuộc
├── requirements-lock.txt                              # Khóa phiên bản phục vụ tái lập
├── experiment_config.json                             # Cấu hình siêu tham số và taxonomy chuẩn
├── build_v3_notebooks.py                              # Script tự động tạo hệ thống Jupyter Notebooks
│
├── data/
│   └── gold_standard_final_48670.csv                 # Tập dữ liệu chuẩn vàng 48,670 dòng
│
├── data_splits/
│   ├── train.csv                                     # 38,936 dòng (80%)
│   ├── dev.csv                                       # 4,867 dòng (10%)
│   ├── test.csv                                      # 4,867 dòng (10% - LOCKED)
│   └── split_manifest.csv                            # Bản đồ phân tầng
│
├── src/
│   ├── data.py                                       # Xử lý dữ liệu, kiểm định và đo độ dài token
│   ├── textcnn.py                                    # Huấn luyện và đánh giá Baseline TextCNN
│   ├── transformer_model.py                          # Định nghĩa Transformer và Smoke Test engine
│   ├── train.py                                      # CLI runner huấn luyện đa mô hình
│   ├── metrics.py                                    # Tính toán Accuracy, F1 Macro/Weighted, CM
│   ├── evaluate.py                                   # Phân tích độ dài, ranh giới lỗi & Bootstrap
│   ├── error_analysis.py                             # Trích xuất ca lỗi thực tế trên Test Set
│   ├── aggregate_results.py                          # Tự động tổng hợp kết quả & report_metrics.json
│   └── plots.py                                      # Sinh biểu đồ chất lượng cao (DPI 300)
│
├── notebooks/
│   ├── 00_data_exploration_and_split.ipynb           # Khám phá EDA, phân chia Stratified Split 80/10/10
│   ├── 01_textcnn.ipynb                              # Huấn luyện & Đánh giá TextCNN
│   ├── 02_phobert.ipynb                              # Huấn luyện & Đánh giá PhoBERT
│   ├── 03_videberta.ipynb                            # Huấn luyện & Đánh giá ViDeBERTa
│   ├── 04_xlmr.ipynb                                 # Huấn luyện & Đánh giá XLM-R
│   ├── 05_compare_models.ipynb                       # So sánh hiệu năng và phân tích lỗi
│   └── DS108_Colab_FineTuning_Transformers_AllInOne.ipynb # Master Colab Notebook chạy 6 experiments
│
├── artifacts/
│   ├── textcnn/                                      # Checkpoints và lịch sử học của TextCNN
│   ├── phobert/                                      # Checkpoints và artifacts của PhoBERT
│   ├── videberta/                                    # Checkpoints và artifacts của ViDeBERTa
│   └── xlmr/                                         # Checkpoints và artifacts của XLM-R
│
├── results/
│   ├── smoke_test_results.json                       # Kết quả kiểm định smoke test
│   ├── token_length_analysis.csv                     # Phân tích phân bố độ dài token trên Train
│   ├── test_results_task1.csv                        # Bảng kết quả Tác vụ 1 trên Test Set
│   ├── test_results_task2.csv                        # Bảng kết quả Tác vụ 2 trên Test Set
│   ├── dev_results.csv                               # Kết quả trên tập Dev (Validation)
│   ├── per_class_metrics.csv                         # Chi tiết Precision/Recall/F1 từng lớp
│   ├── length_analysis.csv                           # Hiệu năng theo 5 nhóm độ dài câu
│   ├── error_cases.csv                               # Danh sách các ca lỗi điển hình
│   ├── predictions/                                  # Chi tiết từng dòng dự đoán trên Test Set
│   └── confusion_matrices/                           # Ma trận nhầm lẫn (CSV)
│
├── figures/                                          # 8 biểu đồ báo cáo khoa học (DPI 300)
│
└── report/
    ├── chuong_4_thuc_nghiem_va_phan_tich_ket_qua.md  # Báo cáo Chương 4 chi tiết chuẩn khóa luận
    ├── experiment_summary.md                         # Tóm tắt thực nghiệm nhanh
    └── report_metrics.json                           # Dữ liệu số liệu đồng bộ cho báo cáo
```

---

## 🚀 Hướng Dẫn Chạy Thực Nghiệm

### 1. Cài đặt môi trường
```bash
pip install -r requirements.txt
```

### 2. Chạy Huấn luyện trên dòng lệnh (CLI)
```bash
# Huấn luyện TextCNN
python src/train.py --model textcnn --task task1
python src/train.py --model textcnn --task task2

# Huấn luyện Transformer (Yêu cầu GPU)
python src/train.py --model phobert --task task1 --batch_size 16 --grad_accum 2
python src/train.py --model videberta --task task1 --batch_size 16 --grad_accum 2
python src/train.py --model xlmr --task task1 --batch_size 16 --grad_accum 2
```

### 3. Huấn luyện toàn bộ trên Google Colab GPU
Mở và chạy file:
`notebooks/DS108_Colab_FineTuning_Transformers_AllInOne.ipynb`

Notebook sẽ tự động:
1. Tải dependencies và kiểm tra GPU T4.
2. Chạy smoke test xác thực.
3. Huấn luyện lần lượt 6 thí nghiệm Transformer cho cả 2 tác vụ.
4. Đánh giá kiểm định từng epoch, khôi phục best checkpoint để đánh giá Test set (chỉ 1 lần duy nhất).
5. Tự động đóng gói toàn bộ thư mục `results/` và `artifacts/` thành file zip để tải về máy.

### 4. Tổng hợp Kết quả và Sinh Báo cáo
Sau khi chạy xong các thí nghiệm:
```bash
python src/aggregate_results.py
```
Lệnh trên sẽ tự động cập nhật toàn bộ các bảng CSV, vẽ lại 8 biểu đồ khoa học trong `figures/` và đồng bộ số liệu vào `report/report_metrics.json`.
