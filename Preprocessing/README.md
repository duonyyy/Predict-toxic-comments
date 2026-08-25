# DS108 Preprocessing

## Cấu trúc thư mục

```text
Preprocessing/
├── config/                  # cấu hình nguồn crawl
├── data/
│   ├── raw/                 # raw.csv, raw.json và snapshot cũ
│   ├── interim/             # output từng bước tiền xử lý
│   ├── processed/           # dataset cuối sau khi hoàn tất pipeline
│   └── audit/               # bảng review/audit, không dùng làm input model
├── docs/
│   ├── guides/              # hướng dẫn kỹ thuật
│   ├── reports/             # báo cáo môn học
│   └── references/          # tài liệu tham khảo
├── notebooks/               # notebook chạy theo thứ tự
├── prompts/                 # prompt và tài nguyên gán nhãn
├── scripts/                 # script có thể chạy từ terminal
└── tests/                   # kiểm thử tự động
```

## Luồng dữ liệu

```text
Crawler/data → data/raw → data/interim → data/processed
```

- `data/raw/`: dữ liệu gốc, không ghi đè bằng bước làm sạch.
- `data/interim/`: snapshot sau các bước làm sạch; notebook 02 xuất file đến bước 5.4.
- `data/processed/`: chỉ dùng khi toàn bộ quy tắc, review và khử trùng ngữ nghĩa đã hoàn tất.
- `data/audit/`: lưu bảng đối chiếu, lý do loại và nhóm trùng; không đưa thẳng vào mô hình.

## Notebook

1. `notebooks/01_eda_raw.ipynb`: khảo sát raw data.
2. `notebooks/02_clearing_data.ipynb`: làm sạch từ 5.1 đến 5.4.
3. `notebooks/03_filter_english_comments.ipynb`: lọc tiếng Anh riêng, nếu cần.
4. `notebooks/04_deduplication_3_levels_colab.ipynb`: khử trùng lặp cấp 1–3 trên Google Colab.

## Chạy merge raw

```powershell
cd C:\Users\Admin\Desktop\DS108\Preprocessing
python -u -X utf8 .\scripts\merge_raw.py
```

Tùy chọn đổi nguồn hoặc output:

```powershell
python -u -X utf8 .\scripts\merge_raw.py `
  --crawler-data "..\Crawler\data" `
  --output-dir ".\data\raw" `
  --sources-config ".\config\sources.json"
```

## Kiểm thử

```powershell
python -m unittest discover -s tests -v
```

## Quy tắc quan trọng

- Chạy khử trùng lặp trước khi chia train/validation/test.
- Dùng deduplication_group_map.csv để chia theo nhóm, tránh data leakage.
- Cấp 3 chỉ xóa sau khi đã review semantic_removal_review.csv.
- Các file audit trong data/audit/ là bằng chứng cho từng quyết định loại.
- Ngưỡng và model được lưu trong config/preprocessing_config.json.
