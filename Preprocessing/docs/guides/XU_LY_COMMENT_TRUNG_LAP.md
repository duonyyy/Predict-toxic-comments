# Xử Lý Comment Trùng Lặp Trong Bộ Dữ Liệu NLP

Tài liệu này trình bày đầy đủ 3 cấp độ kỹ thuật khử trùng lặp (Deduplication) được áp dụng trong tiền xử lý dữ liệu văn bản,
---

## 🔍 Tại Sao Phải Khử Trùng Lặp?

Khi thu thập dữ liệu văn bản từ các nguồn thực tế (crawl forum, mạng xã hội) hoặc khi sử dụng AI để **sinh thêm data** nhằm cân bằng lớp (Class Balancing), dữ liệu thường xuất hiện **2 dạng trùng lặp**:

| Loại trùng lặp | Nguyên nhân | Ví dụ |
|---|---|---|
| **Exact Duplicate** | Crawl nhiều lần, ghép nhiều nguồn | `"Thầy dạy rất hay."` xuất hiện 2 lần giống hệt nhau |
| **Near-Exact Duplicate** | Khác chữ hoa/thường, emoji, dấu câu | `"Trường đẹp!!!"` vs `"trường đẹp"` |


> [!IMPORTANT]
> Không xử lý trùng lặp dẫn đến mô hình bị **overfit** (học thuộc lòng dữ liệu), **metrics bị phồng** (Accuracy ảo), và **test set bị rò rỉ** (Data Leakage).

---

## 🔹 Cấp Độ 1: Khử Trùng Lặp Chính Xác (Exact Match Deduplication)

### Cách hoạt động

So sánh chính xác **100% từng ký tự** giữa các bình luận. Hai câu chỉ bị coi là trùng lặp nếu chuỗi ký tự giống nhau hoàn toàn.

### Khi nào dùng?

- Khi ghép dữ liệu từ nhiều nguồn/file khác nhau.
- Khi crawl dữ liệu từ nhiều thời điểm khác nhau dẫn đến thu thập lại cùng một bài viết.
- Là bước **bắt buộc** trong mọi pipeline tiền xử lý dữ liệu.

### Triển khai bằng Pandas

```python
import pandas as pd

df = pd.read_csv("data.csv")

# Loại bỏ hoàn toàn các dòng có nội dung câu trùng nhau
df = df.drop_duplicates(subset=['sentence'], keep='first')

print(f"Số mẫu sau khi khử trùng lặp: {len(df)}")
```

**Tham số quan trọng:**
- `subset=['sentence']`: Chỉ so sánh cột `sentence` (văn bản), giữ nguyên các cột khác như nhãn.
- `keep='first'`: Giữ lại bản ghi xuất hiện **đầu tiên**, xóa toàn bộ các bản ghi lặp phía sau.
- `keep='last'`: Giữ lại bản ghi xuất hiện **cuối cùng**.
- `keep=False`: Xóa **tất cả** các bản ghi bị lặp kể cả bản gốc.

### Hạn chế

> [!WARNING]
> Cấp độ 1 **không phát hiện** được 2 câu trùng ý nghĩa nhưng khác nhau về chữ hoa/thường, dấu câu, hay emoji.
>
> Ví dụ: `"Trường học rất đẹp!!! 😊"` và `"trường học rất đẹp"` sẽ **không bị xóa** vì chuỗi ký tự không khớp 100%.

---

## 🔹 Cấp Độ 2: Khử Trùng Lặp Sau Chuẩn Hóa (Post-Normalization Deduplication)

### Cách hoạt động

Trước khi so sánh, **chuẩn hóa** tất cả các văn bản về cùng một dạng thống nhất (chữ thường, không dấu câu, không emoji, không khoảng trắng thừa), sau đó mới tiến hành khử trùng lặp.

### Khi nào dùng?

- Khi dữ liệu thu thập từ mạng xã hội (người dùng viết hoa/thường tùy tiện, thêm emoji, thêm dấu chấm cảm...).
- Khi gộp dữ liệu từ các nguồn có quy chuẩn viết khác nhau.

### Vấn đề điển hình

| Comment A | Comment B | `drop_duplicates()` thẳng có xóa không? |
|---|---|---|
| `"Trường học rất đẹp!!! 😊"` | `"trường học rất đẹp"` | ❌ Không xóa |
| `"Thầy   dạy  tốt .."` | `"Thầy dạy tốt"` | ❌ Không xóa |
| `"GV NHIỆT TÌNH"` | `"gv nhiệt tình"` | ❌ Không xóa |

### Quy trình xử lý chuẩn (Best Practice)

```python
import pandas as pd
import re

df = pd.read_csv("data.csv")

# ────────────────────────────────────────────
# Bước 1: Tạo cột văn bản đã chuẩn hóa
# ────────────────────────────────────────────

# 1a. Chuyển thành chữ thường
df['clean_sentence'] = df['sentence'].str.lower()

# 1b. Loại bỏ dấu câu, ký tự đặc biệt và emoji
#     Regex [^\w\s] giữ lại chữ cái Unicode (tiếng Việt) và khoảng trắng
df['clean_sentence'] = df['clean_sentence'].str.replace(
    r'[^\w\s]', '', regex=True
)

# 1c. Chuẩn hóa khoảng trắng thừa
df['clean_sentence'] = df['clean_sentence'].str.strip()
df['clean_sentence'] = df['clean_sentence'].str.replace(
    r'\s+', ' ', regex=True
)

# ────────────────────────────────────────────
# Bước 2: Khử trùng lặp trên cột đã chuẩn hóa
# ────────────────────────────────────────────
df = df.drop_duplicates(subset=['clean_sentence'], keep='first')

# Xóa cột tạm, giữ lại dữ liệu gốc
df = df.drop(columns=['clean_sentence'])

print(f"Số mẫu sau khi khử trùng lặp cấp 2: {len(df)}")
```

### Lưu ý với tiếng Việt có dấu

Regex `[^\w\s]` mặc định của Python giữ lại chữ cái Unicode nên **bảo toàn dấu tiếng Việt** (`ă`, `ê`, `ơ`, `ư`, `đ`...). Nếu muốn lọc chặt hơn, có thể dùng:

```python
import unicodedata

def normalize_vietnamese(text):
    """Giữ lại chữ cái tiếng Việt có dấu, chữ số và khoảng trắng."""
    text = text.lower().strip()
    text = re.sub(r'[^\wàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

df['clean_sentence'] = df['sentence'].apply(normalize_vietnamese)
df = df.drop_duplicates(subset=['clean_sentence'], keep='first')
df = df.drop(columns=['clean_sentence'])
```

---

## 🔹 Cấp Độ 3: Khử Trùng Lặp Mờ / Ngữ Nghĩa (Fuzzy & Semantic Deduplication)

### Cách hoạt động

Phát hiện các câu **có ngữ nghĩa tương tự** dù từ ngữ bề mặt khác nhau. 

### Ví dụ điển hình khi dùng AI sinh data

| Câu | Ngữ nghĩa thực sự |
|---|---|
| `"Cơ sở vật chất của trường rất hiện đại."` | Cơ sở vật chất hiện đại |
| `"Cơ sở vật chất của nhà trường cực kỳ hiện đại."` | Cơ sở vật chất hiện đại |
| `"Trang thiết bị trường học rất tân tiến và hiện đại."` | Cơ sở vật chất hiện đại |

→ Ba câu trên đều diễn đạt **cùng một ý nghĩa** nhưng sẽ không bị bắt bởi Cấp độ 1 hay 2.

---

### Kỹ thuật A: Cosine Similarity trên Vector Embedding (Ngữ nghĩa)

Dùng mô hình Transformer (PhoBERT / Sentence-BERT / Vietnamese Bi-Encoder) chuyển mỗi câu thành một **Vector ngữ nghĩa (Embedding)**, sau đó tính **góc tương tự Cosine** giữa các cặp câu.

> **Nguyên lý:** Hai câu có ý nghĩa gần giống nhau sẽ có vector gần song song → Cosine Similarity cao (gần 1.0).

```python
from sentence_transformers import SentenceTransformer, util
import pandas as pd

df = pd.read_csv("data.csv")
sentences = df['sentence'].tolist()

# ────────────────────────────────────────────
# Bước 1: Tải mô hình Embedding tiếng Việt
# ────────────────────────────────────────────
model = SentenceTransformer('bkai-foundation-models/vietnamese-bi-encoder')

# ────────────────────────────────────────────
# Bước 2: Chuyển câu thành vector embedding
# ────────────────────────────────────────────
print("Đang tính vector embedding...")
embeddings = model.encode(sentences, convert_to_tensor=True, show_progress_bar=True)

# ────────────────────────────────────────────
# Bước 3: Tính ma trận Cosine Similarity
# ────────────────────────────────────────────
cosine_scores = util.cos_sim(embeddings, embeddings)

# ────────────────────────────────────────────
# Bước 4: Lọc bỏ các câu có độ tương tự > 0.90
# ────────────────────────────────────────────
THRESHOLD = 0.90  # Ngưỡng coi là "trùng lặp ngữ nghĩa"

to_remove = set()
for i in range(len(cosine_scores)):
    if i in to_remove:
        continue
    for j in range(i + 1, len(cosine_scores)):
        if cosine_scores[i][j] > THRESHOLD:
            to_remove.add(j)  # Giữ câu i, xóa câu j

# ────────────────────────────────────────────
# Bước 5: Giữ lại các câu không bị trùng lặp
# ────────────────────────────────────────────
df_filtered = df.drop(index=list(to_remove)).reset_index(drop=True)

print(f"Số mẫu ban đầu:         {len(df)}")
print(f"Số mẫu đã bị xóa:       {len(to_remove)}")
print(f"Số mẫu sau khử trùng:   {len(df_filtered)}")
```

**Chọn ngưỡng Cosine Similarity phù hợp:**

| Ngưỡng | Ý nghĩa | Phù hợp khi nào? |
|---|---|---|
| `> 0.95` | Rất giống nhau, gần như là copy | Dataset nhỏ, muốn giữ nhiều đa dạng |
| `> 0.90` | Trùng lặp ngữ nghĩa rõ ràng | **Khuyên dùng** cho data sinh bởi AI |
| `> 0.85` | Tương tự cao, cùng chủ đề | Dataset lớn, cần lọc chặt |

---

### Kỹ thuật B: Khoảng Cách Chuỗi (Levenshtein / Jaccard Distance)

Dùng cho các câu ngắn (< 20 từ) hoặc khi không có GPU để chạy Embedding. So sánh tỷ lệ trùng từ hoặc số lần chỉnh sửa ký tự giữa 2 câu.

#### B1 — Jaccard Similarity (Tỷ lệ trùng từ)

Đo **tỷ lệ từ chung** trên tổng số từ duy nhất của 2 câu:

$$\text{Jaccard}(A, B) = \frac{|A \cap B|}{|A \cup B|}$$

```python
from itertools import combinations
import pandas as pd

def jaccard_similarity(sent_a: str, sent_b: str) -> float:
    """Tính tỷ lệ trùng từ giữa 2 câu theo Jaccard Similarity."""
    set_a = set(sent_a.lower().split())
    set_b = set(sent_b.lower().split())
    if not set_a and not set_b:
        return 1.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)

df = pd.read_csv("data.csv")
sentences = df['sentence'].tolist()

JACCARD_THRESHOLD = 0.85  # Trùng hơn 85% từ → coi là trùng lặp

to_remove = set()
for i, j in combinations(range(len(sentences)), 2):
    if i in to_remove or j in to_remove:
        continue
    score = jaccard_similarity(sentences[i], sentences[j])
    if score > JACCARD_THRESHOLD:
        to_remove.add(j)  # Giữ câu i, xóa câu j

df_filtered = df.drop(index=list(to_remove)).reset_index(drop=True)
print(f"Số mẫu sau khử trùng Jaccard: {len(df_filtered)}")
```

#### B2 — Levenshtein Distance (Số lần chỉnh sửa ký tự)

Đo **số thao tác tối thiểu** (thêm, xóa, thay thế ký tự) để biến câu A thành câu B:

```python
# Cài thư viện: pip install python-Levenshtein
import Levenshtein
from itertools import combinations
import pandas as pd

def levenshtein_similarity(sent_a: str, sent_b: str) -> float:
    """Tính độ tương tự theo Levenshtein (0.0 = khác hoàn toàn, 1.0 = giống hệt)."""
    distance = Levenshtein.distance(sent_a.lower(), sent_b.lower())
    max_len = max(len(sent_a), len(sent_b))
    if max_len == 0:
        return 1.0
    return 1 - (distance / max_len)

df = pd.read_csv("data.csv")
sentences = df['sentence'].tolist()

LEVENSHTEIN_THRESHOLD = 0.85

to_remove = set()
for i, j in combinations(range(len(sentences)), 2):
    if i in to_remove or j in to_remove:
        continue
    score = levenshtein_similarity(sentences[i], sentences[j])
    if score > LEVENSHTEIN_THRESHOLD:
        to_remove.add(j)

df_filtered = df.drop(index=list(to_remove)).reset_index(drop=True)
print(f"Số mẫu sau khử trùng Levenshtein: {len(df_filtered)}")
```

---

## 📊 So Sánh 3 Cấp Độ

| Tiêu chí | Cấp độ 1 (Exact) | Cấp độ 2 (Normalized) | Cấp độ 3A (Semantic) | Cấp độ 3B (Fuzzy) |
|---|:---:|:---:|:---:|:---:|
| **Tốc độ** | ⚡⚡⚡ Rất nhanh | ⚡⚡ Nhanh | 🐢 Chậm (cần GPU) | 🐢 Chậm ($O(n^2)$) |
| **Phát hiện khác chữ hoa/thường** | ❌ | ✅ | ✅ | ✅ |
| **Phát hiện khác dấu câu / emoji** | ❌ | ✅ | ✅ | ✅ |
| **Phát hiện trùng ngữ nghĩa** | ❌ | ❌ | ✅ | ⚠️ Một phần |
| **Yêu cầu GPU** | ❌ | ❌ | ✅ | ❌ |
| **Phù hợp với data AI sinh** | ❌ | ❌ | ✅ ✅ | ✅ |

---

## 🔄 Quy Trình Đầy Đủ (Full Pipeline)

```
┌─────────────────┐
│  Comment Thô    │   (Dữ liệu crawl / AI sinh)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Cấp độ 2: Chuẩn hóa                   │
│  - Chuyển chữ thường (lower)            │
│  - Loại bỏ dấu câu, emoji, ký tự đặc   │
│  - Chuẩn hóa khoảng trắng (strip)      │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│  Cấp độ 1: Exact Drop Duplicates        │
│  df.drop_duplicates(subset=['clean'])   │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│  Cấp độ 3A: Semantic Deduplication      │
│  Embedding + Cosine Similarity > 0.90   │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│  Tập Dataset Cân Bằng & Sạch           │
│  ✅ Không trùng lặp                     │
│  ✅ Đa dạng ngữ nghĩa                   │
│  ✅ Sẵn sàng huấn luyện mô hình         │
└─────────────────────────────────────────┘
```

---

## 💡 Gợi Ý Thực Hành Theo Kịch Bản

| Kịch bản | Cấp độ nên dùng |
|---|---|
| Dữ liệu crawl từ forum / mạng xã hội | Cấp 1 + Cấp 2 |
| Dữ liệu ghép từ nhiều nguồn khác nhau | Cấp 1 + Cấp 2 |
| Dữ liệu do AI (ChatGPT / Gemini) sinh | Cấp 1 + Cấp 2 + **Cấp 3A** |
| Dataset nhỏ (< 5.000 mẫu), không có GPU | Cấp 1 + Cấp 2 + Cấp 3B (Jaccard) |
| Dataset lớn (> 50.000 mẫu) | Cấp 1 + Cấp 2 + Cấp 3A (với batch encoding) |

---

*Tài liệu tham khảo từ mã nguồn các đồ án IE403 và thực tiễn xây dựng bộ dữ liệu NLP tiếng Việt.*
