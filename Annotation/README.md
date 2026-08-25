# Quy trình Annotation DS108

Thư mục này tổ chức toàn bộ tài liệu, prompt, notebook và công cụ cho bài toán
gán nhãn bình luận tiếng Việt.

## Cấu trúc thư mục

```text
Annotation/
├── guidelines/        # Codebook và hướng dẫn annotator
├── prompts/           # Prompt dùng cho LLM
├── schemas/           # JSON Schema kiểm tra output
├── notebooks/         # Notebook Gemini, OpenAI và Qwen3-8B
├── templates/         # Mẫu CSV cho annotator người
├── tools/             # Công cụ IAA và kiểm tra chất lượng
├── research/          # Thiết kế nghiên cứu annotation bằng LLM
├── outputs/           # Kết quả chạy notebook, không phải gold label mặc định
└── README.md
```

## Nguồn chuẩn

`guidelines/label_definitions.md` là codebook duy nhất cho taxonomy:

```text
TOXIC / NON-TOXIC
└── nếu TOXIC: EXPLICIT / IMPLICIT
```

`guidelines/annotation_guideline.md` là tài liệu đầy đủ cho annotator, IAA,
adjudication và kiểm soát chất lượng. `prompts/prompt_dan_nhan_llm.md` là bản
prompt rút gọn, self-contained cho model; không tự tạo taxonomy khác.

## Artifact chính

| File | Vai trò |
|---|---|
| `guidelines/label_definitions.md` | Codebook chuẩn |
| `guidelines/annotation_guideline.md` | Hướng dẫn annotator người |
| `prompts/prompt_dan_nhan_llm.md` | Prompt compact: rules + hard cases + few-shot |
| `schemas/annotation_schema.json` | Schema máy đọc được |
| `templates/pilot_annotation_template.csv` | Template cho annotator độc lập |
| `tools/evaluate_iaa.py` | Raw agreement, Cohen's Kappa và disagreement queue |
| `notebooks/google_annotator_gemini.ipynb` | Gemini batch trên máy cá nhân: retry, checkpoint/resume, review queue |
| `notebooks/chatgpt_annotator_openai.ipynb` | OpenAI tiền dán nhãn |
| `notebooks/qwen3_8b_annotator.ipynb` | Qwen3-8B batch trên Kaggle: checkpoint/resume, review queue, JSON output |
| `research/nghien_cuu_dan_nhan_bang_llm.md` | Thiết kế nghiên cứu và đánh giá |

## Quy trình thực hiện

### Bước 1: Chọn pilot

Lấy mẫu phân tầng theo platform, độ dài, emoji, teencode, tiếng Việt không dấu,
mỉa mai và nhóm duplicate. Không chỉ chọn các câu dễ.

### Bước 2: Gán nhãn độc lập

Tạo hai bản sao từ `templates/pilot_annotation_template.csv`, một cho mỗi
annotator. Hai người gán độc lập, không xem nhãn của nhau và không xem nhãn LLM
trước khi hoàn thành pilot.

### Bước 3: Tính IAA

Chạy từ thư mục `Annotation`:

```powershell
python .\tools\evaluate_iaa.py .\pilot_annotator_a.csv .\pilot_annotator_b.csv `
  --report .\outputs\pilot_iaa_report.json `
  --disagreements .\outputs\pilot_disagreements.csv
```

Script báo cáo riêng cho từng trường nhãn. Cần xem thêm raw agreement, số dòng
thiếu nhãn, tỷ lệ review và các dòng bất đồng; không chỉ nhìn Kappa.

### Bước 4: Adjudication và cập nhật guideline

Đọc `outputs/pilot_disagreements.csv`, quyết định nhãn cuối, ghi lý do ca khó và
cập nhật `guidelines/annotation_guideline.md` nếu một dạng bất đồng lặp lại.
Sau đó tạo gold dataset với phiên bản guideline cụ thể.

### Bước 5: LLM tiền dán nhãn

Chạy một trong các notebook trong `notebooks/` sau khi pilot đã thống nhất. Các
notebook đọc prompt compact và schema dùng chung, lưu kết quả vào `outputs/`.
LLM chỉ đề xuất nhãn và đánh dấu review; không dùng trực tiếp output làm gold.

Qwen3-8B cần GPU CUDA. OpenAI/Gemini cần cấu hình API key và phải xem xét vấn đề
bảo mật khi gửi bình luận mạng xã hội ra dịch vụ bên ngoài.

### Bước 6: Kiểm tra chất lượng

Sau khi có gold dataset, cần báo cáo:

- phân bố `TOXIC/NON-TOXIC`;
- phân bố `EXPLICIT/IMPLICIT` trên tập `TOXIC`;
- raw agreement, Cohen's Kappa hoặc Krippendorff's Alpha;
- precision, recall, F1 và confusion matrix của LLM so với gold;
- kết quả theo platform, độ dài, emoji, teencode, nhóm xã hội và ngữ cảnh;
- số lượng duplicate, bản ghi rỗng, review và bất đồng;
- kiểm tra leakage trước khi chia train/dev/test.

## Nguyên tắc không được vi phạm

- Chỉ dùng bốn khái niệm trong codebook; không thêm nhãn cảm xúc, category hoặc
  nhãn tự tạo khác vào output.
- Không suy diễn ngữ cảnh không được cung cấp.
- Không để LLM quyết định gold label một mình.
- Không ghi API key vào log, checkpoint hoặc file output.
- Không chia duplicate/near-duplicate hoặc cùng nhóm bài đăng sang nhiều split.
- Mọi thay đổi codebook phải tăng version và đánh giá lại mẫu bị ảnh hưởng.
