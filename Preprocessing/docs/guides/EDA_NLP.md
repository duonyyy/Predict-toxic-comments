# EDA cho dữ liệu NLP mạng xã hội

## 1. Mục tiêu

Exploratory Data Analysis (EDA) là bước khảo sát dữ liệu trước khi làm sạch sâu, gắn nhãn hoặc huấn luyện mô hình. Với dữ liệu title và comment, EDA cần trả lời:

- Dữ liệu có đủ, đúng kiểu và đúng thời gian không?
- Có bao nhiêu bản ghi rỗng, lỗi, trùng hoặc gần trùng?
- Nội dung phân bố thế nào theo nền tảng, ngôn ngữ và thời gian?
- Comment có đặc điểm gì về độ dài, emoji, URL, mention và hashtag?
- Nhãn cảm xúc, chủ đề hoặc spam có mất cân bằng không?
- Có nguy cơ rò rỉ dữ liệu giữa train, validation và test không?

EDA không thay thế bước gắn nhãn hay đánh giá mô hình. Word cloud chỉ mang tính minh họa, không đủ để kết luận về chủ đề hoặc cảm xúc.

## 2. Nguyên tắc

```
Kiểm kê schema
→ kiểm tra chất lượng
→ khảo sát trùng lặp
→ phân tích văn bản
→ phân tích thời gian và tương tác
→ kiểm tra nhãn
→ kiểm tra rò rỉ dữ liệu
→ ghi nhận phát hiện và hành động xử lý
```

1. Giữ dữ liệu gốc trong raw_text hoặc text_raw.
2. Không sửa dữ liệu chỉ để làm biểu đồ.
3. Lưu số lượng bản ghi ở đầu và cuối mỗi bước.
4. Tách thống kê mô tả khỏi quyết định xóa dữ liệu.
5. Ẩn danh hoặc hash thông tin người dùng trước khi xuất báo cáo.

## 3. Schema đề xuất

| Trường | Ý nghĩa |
|---|---|
| platform | Nền tảng nguồn |
| post_id | Mã bài đăng |
| comment_id | Mã bình luận |
| parent_comment_id | Mã bình luận cha |
| title | Tiêu đề hoặc nội dung bài đăng |
| comment | Nội dung bình luận |
| raw_text | Văn bản chưa xử lý |
| clean_text | Văn bản đã xử lý |
| created_at | Thời điểm đăng |
| crawl_time | Thời điểm thu thập |
| author_id | Mã người dùng đã ẩn danh |
| like_count, reply_count | Chỉ số tương tác |
| language | vi, en, mixed hoặc unknown |
| sentiment, topic, intent | Nhãn phân tích |
| is_spam | Cờ spam |

Không phải dataset nào cũng có đủ các trường. Cần ghi rõ trường thực sự có mặt thay vì tự suy diễn giá trị thiếu.

## 4. Nạp dữ liệu và kiểm kê

```python
import re
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

sns.set_theme(style="whitegrid")
df = pd.read_parquet("data.parquet")  # hoặc pd.read_csv("data.csv")
df = df.copy()

text_col = "comment"
if text_col not in df.columns:
    raise ValueError(f"Thiếu cột bắt buộc: {text_col}")

df["text_for_eda"] = df[text_col].fillna("").astype(str)
if "created_at" in df.columns:
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

print("Số dòng:", len(df))
print("Số cột:", len(df.columns))
display(df.head(3))
```

Bảng kiểm kê chất lượng:

```python
schema = pd.DataFrame({
    "dtype": df.dtypes.astype(str),
    "missing": df.isna().sum(),
    "missing_rate": df.isna().mean().round(4),
    "n_unique": df.nunique(dropna=False),
})
display(schema.sort_values("missing_rate", ascending=False))

is_blank = df[text_col].isna() | df[text_col].astype("string").str.strip().eq("")
print("Thiếu:", df[text_col].isna().sum())
print("Rỗng hoặc chỉ có khoảng trắng:", is_blank.sum())
```

Không tự động coi mọi comment ngắn là vô ích. Các câu như ghét, tuyệt hoặc buồn quá có thể chứa tín hiệu cảm xúc mạnh.

## 5. Trùng lặp và định danh

```python
for col in ["post_id", "comment_id", "parent_comment_id"]:
    if col in df.columns:
        print(col, "trống:", df[col].isna().sum(),
              "trùng:", df[col].duplicated().sum())

print("Tỷ lệ nội dung trùng tuyệt đối:",
      round(df[text_col].duplicated(keep=False).mean(), 4))
```

Phân biệt trùng theo comment_id, trùng tuyệt đối theo nội dung, trùng sau chuẩn hóa và trùng mờ/ngữ nghĩa. Khóa chuẩn hóa chỉ dùng để phân tích, không ghi đè văn bản gốc:

```python
def make_dedup_key(text):
    text = str(text).lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

df["dedup_key"] = df["text_for_eda"].map(make_dedup_key)
duplicate_summary = df["dedup_key"].value_counts()
print("Số nhóm trùng sau chuẩn hóa:",
      (duplicate_summary > 1).sum())
```

Không nên xóa ngay các bản ghi gần giống. Câu khác phủ định, emoji hoặc sắc thái cảm xúc có thể vẫn là mẫu hợp lệ.

## 6. Đặc trưng văn bản

```python
df["char_count"] = df["text_for_eda"].str.len()
df["word_count"] = df["text_for_eda"].str.split().str.len()
df["exclamation_count"] = df["text_for_eda"].str.count("!")
df["question_count"] = df["text_for_eda"].str.count(r"\?")
df["repeated_char"] = df["text_for_eda"].str.contains(
    r"(.)\1{2,}", regex=True
)

URL_RE = r"https?://\S+|www\.\S+"
MENTION_RE = r"(?<!\w)@\w+"
HASHTAG_RE = r"(?<!\w)#\w+"
PHONE_RE = r"(?<!\d)(?:\+?84|0)\d{8,10}(?!\d)"

df["url_count"] = df["text_for_eda"].str.count(URL_RE)
df["mention_count"] = df["text_for_eda"].str.count(MENTION_RE)
df["hashtag_count"] = df["text_for_eda"].str.count(HASHTAG_RE)
df["phone_count"] = df["text_for_eda"].str.count(PHONE_RE)

display(df[[
    "char_count", "word_count", "url_count", "mention_count",
    "hashtag_count", "phone_count"
]].describe(percentiles=[.01, .05, .5, .95, .99]).T)
```

Emoji nên được thống kê trước khi quyết định loại bỏ:

```python
def count_emoji(text):
    return sum(ord(char) > 0x1F000 for char in text)

df["emoji_count"] = df["text_for_eda"].map(count_emoji)
```

Hàm trên chỉ là xấp xỉ; emoji gồm nhiều code point cần thư viện chuyên dụng nếu yêu cầu độ chính xác cao.

## 7. Phân tích độ dài, nền tảng và thời gian

```python
display(df[["char_count", "word_count"]].describe(
    percentiles=[.01, .05, .25, .5, .75, .95, .99]
).T)

fig, axes = plt.subplots(1, 2, figsize=(13, 4))
sns.histplot(df["char_count"], bins=50, ax=axes[0])
axes[0].set_title("Phân bố số ký tự")
sns.histplot(df["word_count"], bins=50, ax=axes[1])
axes[1].set_title("Phân bố số từ")
plt.tight_layout()
```

```python
if "platform" in df.columns:
    platform_summary = (
        df.groupby("platform", dropna=False)
          .agg(records=(text_col, "size"),
               median_chars=("char_count", "median"))
          .sort_values("records", ascending=False)
    )
    display(platform_summary)

if "created_at" in df.columns:
    df["date"] = df["created_at"].dt.date
    df["hour"] = df["created_at"].dt.hour
    daily = df.groupby("date", dropna=False).size()
    hourly = df.groupby("hour", dropna=False).size()
```

Không nên gộp các nền tảng trước khi EDA. Cần kiểm tra múi giờ và crawl_time vì một đỉnh bất thường có thể do crawler chạy lại.

## 8. Tương tác và người dùng

```python
interaction_cols = [
    c for c in ["like_count", "reply_count"] if c in df.columns
]
for col in interaction_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")
    df[f"log_{col}"] = np.log1p(df[col].clip(lower=0))

if interaction_cols:
    display(df[interaction_cols].describe(
        percentiles=[.5, .9, .95, .99]
    ).T)
```

Lượt thích và phản hồi thường lệch phải, nên xem trung vị và các phân vị cao. Nếu có author_id đã ẩn danh, có thể thống kê số comment theo người dùng để phát hiện hoạt động bất thường; không xuất định danh gốc.

## 9. Ngôn ngữ, spam và nội dung rác

```python
for col in ["language", "is_spam"]:
    if col in df.columns:
        display(df[col].value_counts(dropna=False).to_frame("records"))
```

Nên phân tích:

- Tiếng Việt có dấu, không dấu, tiếng Anh và nội dung trộn ngôn ngữ.
- Comment chỉ có URL, mention, hashtag hoặc emoji.
- Comment chứa số điện thoại, email hoặc lời kêu gọi mua hàng.
- Nội dung copy-paste trên nhiều bài đăng.
- Chuỗi quá ngắn hoặc chỉ gồm ký hiệu.

Nên tạo cờ is_only_url, is_only_emoji, is_spam và spam_reason thay vì xóa ngay. Comment chỉ có emoji có thể là dữ liệu hợp lệ cho phân tích cảm xúc.

## 10. Nhãn và rò rỉ dữ liệu

```python
for col in ["sentiment", "topic", "intent", "is_spam"]:
    if col in df.columns:
        summary = df[col].value_counts(dropna=False).rename("records").to_frame()
        summary["rate"] = summary["records"] / len(df)
        display(summary)

if "sentiment" in df.columns:
    display(df.groupby("sentiment")[
        ["char_count", "word_count", "emoji_count"]
    ].agg(["count", "median", "mean"]))
```

Nếu một nhãn gần như chỉ xuất hiện ở một nền tảng, một thời kỳ hoặc một nhóm tác giả, mô hình có thể học tín hiệu phụ thay vì nội dung.

Trước khi chia train/validation/test, cần kiểm tra:

- Cùng comment_id xuất hiện ở nhiều tập.
- Cùng post_id xuất hiện ở train và test.
- Cùng author_id xuất hiện ở nhiều tập khi hành vi người dùng tạo tín hiệu mạnh.
- Các bản ghi trùng hoặc gần trùng bị chia sang nhiều tập.

Khi có post_id, nên cân nhắc chia theo bài đăng. Toàn bộ nhóm trùng nên nằm trong cùng một split.

## 11. Từ khóa và chủ đề

```python
from sklearn.feature_extraction.text import CountVectorizer

vectorizer = CountVectorizer(
    ngram_range=(1, 2),
    min_df=5,
    max_df=0.95,
    max_features=100,
)
X = vectorizer.fit_transform(df["text_for_eda"])
counts = pd.Series(
    X.sum(axis=0).A1,
    index=vectorizer.get_feature_names_out()
)
display(counts.sort_values(ascending=False).head(30).to_frame("count"))
```

Khi chưa có nhãn chủ đề:

```text
clean_text
→ embedding
→ clustering
→ từ khóa đại diện
→ đặt tên chủ đề
→ kiểm tra thủ công
```

Word cloud chỉ nên dùng để minh họa. Cần xem comment đại diện và từ khóa theo cụm để tránh kết luận sai ngữ cảnh.

## 12. Phân tích title–comment

```python
if {"title", "comment"}.issubset(df.columns):
    title_key = df["title"].fillna("").astype(str).str.lower().str.strip()
    comment_key = df["comment"].fillna("").astype(str).str.lower().str.strip()
    df["title_equals_comment"] = (
        title_key.eq(comment_key) & title_key.ne("")
    )
    print("Tỷ lệ title trùng comment:",
          round(df["title_equals_comment"].mean(), 4))
```

Tỷ lệ cao có thể cho thấy dữ liệu bị sao chép hoặc crawler lấy sai trường. Cần kiểm tra mẫu thủ công trước khi xóa.

## 13. Bộ biểu đồ và đầu ra tối thiểu

Nên có:

1. Số bản ghi theo nền tảng.
2. Tỷ lệ thiếu theo cột.
3. Phân bố độ dài ký tự và số từ.
4. Số bản ghi theo ngày và theo giờ.
5. Tỷ lệ ngôn ngữ.
6. Tỷ lệ exact duplicate và near-duplicate.
7. Phân bố nhãn cảm xúc, chủ đề và spam.
8. Phân bố lượt thích và phản hồi sau log1p.
9. Top unigram/bigram sau chuẩn hóa.
10. Tỷ lệ nhãn theo nền tảng và thời gian.

Mỗi biểu đồ cần có tiêu đề, đơn vị, khoảng thời gian và số mẫu n.

Nên lưu:

```text
eda_schema.csv
eda_quality_summary.csv
eda_platform_summary.csv
eda_time_summary.csv
eda_text_statistics.csv
eda_label_distribution.csv
eda_duplicate_summary.csv
eda_figures/
eda_findings.md
```

## 14. Mẫu bảng kết luận EDA

| Phát hiện | Bằng chứng | Rủi ro | Hành động |
|---|---|---|---|
| Comment rỗng | Tỷ lệ rỗng theo cột | Đầu vào không có nghĩa | Gắn cờ và loại trước huấn luyện |
| Trùng theo ID | Số comment_id lặp | Crawl lặp | Giữ theo quy tắc nguồn |
| Độ dài lệch phải | P99 lớn hơn nhiều trung vị | Dữ liệu lỗi hoặc ngoại lệ | Kiểm tra mẫu, không cắt tùy tiện |
| Nhãn mất cân bằng | Tỷ lệ nhãn lớn nhất/nhỏ nhất | Accuracy gây hiểu nhầm | Dùng stratify và macro-F1 |
| Đỉnh theo thời gian | Tăng đột biến trong một giờ | Crawler hoặc sự kiện thật | Đối chiếu thời gian crawl |
| Nhiều nội dung lặp | Tỷ lệ duplicate cao | Overfit và leakage | Khử trùng trước khi chia tập |

## 15. Checklist

- [ ] Đã kiểm tra schema, kiểu dữ liệu và múi giờ.
- [ ] Đã thống kê thiếu, rỗng, lỗi mã hóa và định danh trùng.
- [ ] Đã đo độ dài bằng ký tự và từ/token.
- [ ] Đã thống kê URL, mention, hashtag, emoji và thông tin nhạy cảm.
- [ ] Đã so sánh dữ liệu theo nền tảng và thời gian.
- [ ] Đã khảo sát phân bố tương tác và ngoại lệ.
- [ ] Đã kiểm tra ngôn ngữ, spam và copy-paste.
- [ ] Đã kiểm tra phân bố nhãn và mất cân bằng.
- [ ] Đã kiểm tra trùng lặp trước khi chia tập.
- [ ] Đã ghi lại phát hiện, bằng chứng và hành động xử lý.
- [ ] Đã ẩn danh dữ liệu cá nhân trong báo cáo.

## 16. Kết luận

EDA cho dữ liệu NLP mạng xã hội cần kết hợp thống kê cấu trúc, chất lượng dữ liệu, đặc trưng ngôn ngữ, hành vi tương tác, thời gian và nhãn. Trọng tâm là phát hiện crawler lặp dữ liệu, mất cân bằng nhãn, ngôn ngữ hỗn hợp, spam, lệch nguồn và rò rỉ giữa các tập.

Kết quả EDA nên được dùng để quyết định quy tắc làm sạch, chiến lược chia dữ liệu, cách gắn nhãn và thiết kế thí nghiệm mô hình; không nên dùng để hợp thức hóa việc xóa dữ liệu mà không có bằng chứng.
