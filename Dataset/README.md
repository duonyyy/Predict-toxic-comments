# 📦 BỘ DỮ LIỆU SẠCH (DATASET) - DS108

Thư mục lưu trữ 2 tệp dữ liệu cốt lõi đã qua xử lý hoàn chỉnh và gán nhãn chuẩn vàng của đồ án **DS108**:

---

## 🗂️ Danh Sách Các Tệp Dữ Liệu

### 1. 🌟 Bộ Dữ Liệu Chuẩn Vàng Gán Nhãn Đầy Đủ (Gold Standard Dataset)
- **Tệp:** [`dataset.csv`](file:///c:/Users/Admin/Desktop/DS108/Dataset/dataset.csv)
- **Kích thước:** 48,670 dòng (~9.72 MB)
- **Cấu trúc cột:**
  - `row_id`: Mã định danh duy nhất của bình luận.
  - `comment`: Nội dung bình luận đã qua làm sạch và chuẩn hóa văn bản.
  - `toxicity`: Nhãn Tầng 1 (`TOXIC` / `NON-TOXIC`).
  - `expression_type`: Nhãn Tầng 2 (`EXPLICIT` / `IMPLICIT` / để trống nếu NON-TOXIC).
  - `evidence`: Căn cứ / Giải thích gán nhãn.

---

### 2. 🧹 Bộ Ngữ Liệu Bình Luận Đã Làm Sạch (Cleaned Text Corpus)
- **Tệp:** [`final_cleaned_comments.csv`](file:///c:/Users/Admin/Desktop/DS108/Dataset/final_cleaned_comments.csv)
- **Kích thước:** 48,670 dòng (~5.36 MB)
- **Nội dung:** Toàn bộ bình luận đã qua 5 bước tiền xử lý (loại bỏ nhiễu, lọc spam, chuẩn hóa teencode/icon/emoji, khử trùng lặp đa tầng).
- **Cấu trúc cột:** `row_id`, `comment`.

---

## 📊 Thống Kê Phân Bố Nhãn

```text
Tổng số mẫu: 48,670 mẫu
├── NON-TOXIC: ~75.4% (36,698 mẫu)
└── TOXIC:     ~24.6% (11,972 mẫu)
    ├── EXPLICIT (Độc hại trực tiếp)
    └── IMPLICIT (Độc hại ẩn ý / mỉa mai)
```
