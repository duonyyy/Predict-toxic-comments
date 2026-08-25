# PHƯƠNG PHÁP XỬ LÝ VÀ TIỀN XỬ LÝ DỮ LIỆU VĂN BẢN TIẾNG VIỆT

## 1. Mục tiêu

Quy trình này được xây dựng nhằm làm sạch và chuẩn hóa dữ liệu văn bản tiếng
Việt từ nhiều nền tảng mạng xã hội trước khi đưa vào các bước phân tích tiếp
theo.

Mục tiêu chính gồm:

- Loại bỏ dữ liệu lỗi, rỗng, trùng lặp hoặc không liên quan.
- Tạo một dataset sạch, thống nhất và có thể tái sử dụng cho nhiều mục đích.

---

## 2. Dữ liệu đầu vào

Sau bước merge, dữ liệu của project có các trường chính:

```text
row_id
platform
title
comment
```



Cần giữ riêng văn bản gốc và văn bản sau xử lý trong phạm vi phù hợp:

```text
text_raw
text_clean
```

`text_raw` chỉ được giữ trong kho nội bộ có quyền truy cập hạn chế. Mọi file
dùng để huấn luyện, chia sẻ hoặc báo cáo phải dùng `text_clean` và không chứa
username, tên được tag, URL cá nhân, email hoặc số điện thoại. Nếu chính sách
quyền riêng tư yêu cầu xóa hoàn toàn, phải xóa cả bản raw sau khi hoàn tất kiểm
tra cần thiết.

---

## 3. Quy trình xử lý dữ liệu

### 3.1. Kiểm tra giá trị thiếu và bình luận rỗng

Loại bỏ các bản ghi thuộc một trong các trường hợp:

- Giá trị `NaN` hoặc `None`.
- Chuỗi rỗng.
- Chuỗi chỉ chứa khoảng trắng.

Ví dụ:

```python
df = df.dropna(subset=["comment"])
df["comment"] = df["comment"].astype(str).str.strip()
df = df[df["comment"] != ""]
```

Sau mỗi bước tiền xử lý, cần kiểm tra lại để loại các câu không còn token có ý nghĩa.

---

### 3.2. Lọc ngôn ngữ

Đối với dữ liệu tổng hợp hoặc dữ liệu thu thập từ nhiều nguồn, có thể dùng `langdetect` để chỉ giữ lại các câu được nhận diện là tiếng Việt.

```python
from langdetect import detect

def detect_language(text):
    try:
        return detect(text)
    except Exception:
        return "unknown"

df["language"] = df["comment"].apply(detect_language)
```

Nên lưu các nhóm ngôn ngữ chi tiết hơn:

```text
vi          : tiếng Việt chủ yếu
en          : tiếng Anh chủ yếu
mixed       : trộn tiếng Việt và tiếng Anh
emoji_only  : chỉ có emoji/ký hiệu cảm xúc
unknown     : không xác định được
```

Không tự động xóa `mixed`, `emoji_only` hoặc `unknown`; các nhóm này cần được
thống kê và review trước khi quyết định lọc.

Không nên tự động loại tất cả câu ngắn hoặc câu có xen tiếng Anh vì bộ phát hiện ngôn ngữ có thể dự đoán sai. Các trường hợp không chắc chắn nên được kiểm tra thủ công.

Bước lọc ngôn ngữ được sử dụng trong một notebook nhưng không xuất hiện trong notebook còn lại.

---

### 3.3. Loại văn bản quá ngắn và không có ý nghĩa

Loại các mẫu chỉ gồm:

- Ký tự đặc biệt hoặc dấu câu.
- Một URL.
- Một thẻ gắn tên người dùng.
- Chuỗi ký tự rác.
- Trợ từ hoặc từ đệm không thể hiện nội dung rõ ràng.

Không nên chỉ dùng ngưỡng số ký tự để xóa dữ liệu vì các câu ngắn như:

```text
tuyệt
ghét
cảm ơn
buồn quá
```

vẫn có thể mang tín hiệu cảm xúc quan trọng.

Nên kết hợp luật tự động với danh sách ngoại lệ và kiểm tra thủ công.


### 3.5. Xóa thông tin cá nhân và thông tin nhận dạng

Để bảo vệ quyền riêng tư, các thông tin nhận dạng phải được xóa khỏi
`text_clean`, không thay bằng token chung. Các trường cần xóa gồm:

```text
mention dạng @tên_người_dùng → [xóa]
URL            → [xóa]
email          → [xóa]
số điện thoại  → [xóa]
hình ảnh        → [xóa]
tên người được tag hoặc mention → [xóa]
```

Ví dụ:

```text
@nam xem video này đi
→ xem video này đi

```

Không đưa `username`, tên người được tag, mention dạng `@tên_người_dùng`, email,
số điện thoại hoặc URL cá nhân
vào dataset dùng để huấn luyện. `comment_id` và các ID nguồn chỉ nên giữ trong
metadata nội bộ nếu thực sự cần phân biệt các bản ghi.

Sau khi xóa thông tin nhận dạng, cần chuẩn hóa lại khoảng trắng và kiểm tra câu
có trở thành rỗng hay không. Nếu `text_clean` chỉ còn khoảng trắng hoặc không
còn token có ý nghĩa, đánh dấu `empty_after_pii_removal` và loại khỏi tập huấn
luyện. Việc xóa tên phải được kiểm tra để không làm mất phần nội dung còn lại
của comment.

---

### 3.6. Phát hiện quảng cáo, spam và nội dung không liên quan

Loại các mẫu có đặc điểm rõ ràng như:

- Nội dung bán hàng hoặc quảng cáo không liên quan.
- Chứa URL, số điện thoại hoặc lời kêu gọi mua hàng với mật độ cao.
- Nội dung được đăng lặp lại hàng loạt.
- Chỉ chứa tag, link hoặc thông tin quảng bá.
- Không có quan hệ rõ ràng với chủ đề của bài đăng.

Có thể kết hợp:

- Luật từ khóa.
- Kiểm tra tỷ lệ URL, số điện thoại và hashtag.
- Phát hiện mẫu lặp.
- Bộ phân loại spam.
- Kiểm tra thủ công.

Việc xác định “lạc đề” cần dựa trên cả nội dung bài đăng và bình luận. Nếu dữ
liệu không lưu `title`, `post_id` hoặc nội dung bài đăng, không được tự động
loại theo chủ đề; chỉ loại các mẫu spam/quảng cáo rõ ràng theo luật đã thống
nhất.

---

### 3.7. Chuẩn hóa Unicode và khoảng trắng

Chuẩn hóa Unicode về NFC, xóa khoảng trắng đầu cuối và gộp nhiều khoảng trắng liên tiếp.

```python
import re
import unicodedata

def normalize_unicode_whitespace(text):
    text = unicodedata.normalize("NFC", str(text))
    text = re.sub(r"\s+", " ", text).strip()
    return text
```

Ví dụ:

```text
"  phim   này hay  "
→ "phim này hay"
```

---

### 3.8. Chuyển về chữ thường

Hai notebook đều chuyển token về chữ thường.

```python
text = text.lower()
```

Ví dụ:

```text
"Phim Này Hay"
→ "phim này hay"
```

---

### 3.9. Chuẩn hóa ký tự đặc biệt nhưng giữ emoji

Không dùng biểu thức chính quy để xóa toàn bộ ký tự đặc biệt trên
`text_clean`, vì cách này sẽ xóa emoji và dấu câu có giá trị cảm xúc. Các emoji
sau phải được giữ nguyên, không xóa và không biến đổi:

```text
✅ ❤ 😂 😭 🥰 🤣 👍
```

Ký tự biến thể của emoji, ví dụ `❤` và `❤️`, cũng không được tự ý loại bỏ.

Cấu hình mặc định chỉ nên chuẩn hóa Unicode và khoảng trắng:

```python
import re
import unicodedata

def normalize_text_keep_emoji(text):
    text = unicodedata.normalize("NFC", str(text))
    return re.sub(r"\s+", " ", text).strip()
```

---

### 3.10. Xử lý emoji: giữ nguyên mặc định

Emoji là tín hiệu cảm xúc nên cấu hình chính phải giữ nguyên:

1. Không xóa emoji.
2. Không rút gọn chuỗi emoji lặp.
3. Không chuyển emoji thành mô tả văn bản.

Ví dụ:

```text
😂😂😂😂😂 → 😂😂😂😂😂
😭 → 😭
✅ ❤ 🥰 🤣 👍 → ✅ ❤ 🥰 🤣 👍
```

Không xóa các bình luận chỉ có emoji nếu emoji thể hiện cảm xúc rõ ràng.
Nếu muốn thử rút gọn hoặc chuyển emoji thành token, tạo một phiên bản dữ liệu
thí nghiệm riêng; không thay đổi `text_clean` mặc định.

```text
😭
😂😂
❤️
```


### 3.14. Xóa dữ liệu trùng lặp

Việc phát hiện trùng nên thực hiện trên một cột khóa chuẩn hóa riêng, không ghi đè văn bản đầu vào.

#### Trùng theo định danh

Nếu hai bản ghi có cùng `platform` và `comment_id`, chúng được xem là cùng một bình luận.

#### Trùng hoàn toàn theo nội dung

Tạo khóa bằng cách:

```text
chuẩn hóa Unicode
→ chuyển chữ thường
→ gộp khoảng trắng
→ dùng comment sau khi đã xóa thông tin cá nhân
→ giữ nguyên emoji và dấu câu trong khóa chính
```

Nếu còn định danh nguồn, chỉ loại bản ghi khi cùng khóa ID. Nếu chỉ còn
`raw.csv` 4 cột, xuất các nhóm trùng để review thay vì xóa tự động.

```python
duplicate_mask = df.duplicated("dedup_key", keep=False)
review_duplicates = df.loc[duplicate_mask]
```

#### Trùng sau xóa thông tin cá nhân

Ví dụ:

```text
@nam xem video này đi
@linh xem video này đi
```

Sau khi xóa tên người dùng:

```text
xem video này đi
xem video này đi
```

Các câu này nên được đưa vào nhóm `template_duplicate` để kiểm tra riêng.
Chúng có thể là hai bình luận thật của hai người dùng khác nhau, không nhất
thiết là bản ghi bị thu thập hai lần.

#### Gần trùng

Ví dụ:

```text
phim này hay quá :)))
phim này hay quá :))))
phim này hay quá trờiiii :))))
```

Có thể dùng:

- Levenshtein similarity.
- Jaccard similarity trên character n-gram.
- Cosine similarity trên sentence embedding.

Các trường hợp gần trùng nên được gom cụm và kiểm tra thủ công trước khi xóa.

Không nên xem hai câu khác emoji hoặc từ phủ định là tương đương:

```text
hay quá 😂
hay quá 😒
```

---

### 3.15. Kiểm tra câu rỗng sau tiền xử lý

Sau khi xóa thông tin cá nhân, chuẩn hóa và xử lý token, cần xóa các câu trở
thành rỗng. Không xóa comment chỉ có emoji hợp lệ.

```python
processed = [process_sentence(x) for x in X]
keep = [bool(x.strip()) for x in processed]

X_clean = [x for x, ok in zip(processed, keep) if ok]
y_clean = [y for y, ok in zip(y, keep) if ok]
```

Trong một notebook, mã nguồn có ý định dùng `np.delete` để xóa câu rỗng nhưng không gán lại kết quả, nên thao tác này chưa thực sự thay đổi dữ liệu. Khi triển khai lại, cần dùng mặt nạ lọc hoặc gán lại mảng mới.


## 3.16. Báo cáo chất lượng dữ liệu trước khi làm sạch

Trước khi xóa hoặc biến đổi dữ liệu, cần tạo một báo cáo chất lượng để biết
pipeline đang tác động lên bao nhiêu bản ghi. Tối thiểu nên thống kê:

```text
tổng số dòng
số dòng theo platform
số comment rỗng
độ dài comment nhỏ nhất/trung bình/lớn nhất
số URL, hashtag, mention và emoji
phân bố language
số nhóm dedup_candidate
```

Ví dụ:

```python
import json
from pathlib import Path

comments = df["comment"].fillna("").astype(str)
quality_report = {
    "rows": int(len(df)),
    "rows_by_platform": df["platform"].fillna("unknown").value_counts().to_dict(),
    "empty_comments": int(comments.str.strip().eq("").sum()),
    "comment_length": {
        "min": int(comments.str.len().min()),
        "mean": float(comments.str.len().mean()),
        "max": int(comments.str.len().max()),
    },
    "url_candidates": int(comments.str.contains(r"https?://|www\.", regex=True).sum()),
    "mention_candidates": int(comments.str.contains("@", regex=False).sum()),
    "emoji_rows": int(comments.str.contains("✅|❤|😂|😭|🥰|🤣|👍", regex=True).sum()),
}

Path("Preprocessing/data/quality_report.json").write_text(
    json.dumps(quality_report, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
```

Báo cáo này chỉ thống kê, không tự động xóa comment ngắn, comment chỉ có emoji
hoặc các nhóm ngôn ngữ chưa chắc chắn.

---






## 6. Ghi nhận quá trình làm sạch

Không xóa dữ liệu mà không ghi lại lý do. Nên lưu các trường audit riêng:

```text
is_removed
removal_reason
duplicate_group_id
```

Các lý do có thể gồm:

```text
empty
unknown_language
too_short
empty_after_pii_removal
advertisement
spam
off_topic
duplicate
near_duplicate_candidate
template_duplicate_candidate
```

Nên công bố số lượng bản ghi trước và sau từng bước để kiểm tra việc làm sạch
không làm mất dữ liệu ngoài dự kiến.

Các file kết quả nên phân biệt rõ vai trò:

```text
quality_report.json       # thống kê chất lượng
raw_dedup_review.csv      # ứng viên trùng cần review
```

---

## 7. Quy trình tổng thể

```text
Dữ liệu thô
→ lưu văn bản gốc
→ tạo quality_report.json
→ xóa giá trị thiếu và bình luận rỗng
→ lọc ngôn ngữ tiếng Việt
→ loại văn bản quá ngắn không có ý nghĩa
→ xóa username, URL và thông tin cá nhân
→ loại quảng cáo, spam và nội dung lạc đề theo luật đã xác định
→ chuẩn hóa Unicode và khoảng trắng
→ chuyển về chữ thường
→ tạo khóa phát hiện trùng
→ tạo nhóm duplicate candidate để review
→ chỉ xóa bản ghi được xác nhận là crawl trùng
→ xóa câu rỗng sau tiền xử lý
```


---

## 8. Căn cứ và mức độ xác nhận




Các bước trong tài liệu gồm cả phần đã có trong pipeline và phần khuyến nghị mở
rộng. Cần kiểm tra mã nguồn chạy thực tế trước khi gọi một bước là đã triển
khai. Đặc biệt, một notebook rỗng hoặc chưa chạy không phải là bằng chứng của
một quy trình đã hoạt động.

Các nguyên tắc bắt buộc của dataset này là:

- Giữ nguyên emoji, bao gồm `✅ ❤ 😂 😭 🥰 🤣 👍`.
- Xóa thông tin cá nhân khỏi dữ liệu dùng để huấn luyện.
- Loại spam và quảng cáo khi đã khớp luật rõ ràng; không dùng cùng luật đó để
  loại các comment hợp lệ chỉ vì giống nội dung.
- Tạo báo cáo chất lượng trước và sau xử lý.

---

## 9. Khử trùng lặp phù hợp với `Preprocessing/data/raw/raw.csv`

`raw.csv` hiện chỉ có:

```text
row_id, platform, title, comment
```

Raw không có `comment_id`, `post_id` hoặc `content_id`. Ngoài ra, `row_id` được
tạo lại mỗi lần merge nên không phải định danh ổn định. Vì vậy, không thể khẳng
định hai comment giống nội dung là cùng một bản ghi bị crawl trùng.

### 9.1. Tạo khóa review an toàn

Khóa này chỉ chuẩn hóa Unicode, chữ hoa/thường và khoảng trắng. Emoji, dấu câu
và nội dung comment vẫn được giữ nguyên:

```python
from pathlib import Path
import re
import unicodedata
import pandas as pd

RAW_PATH = Path("Preprocessing/data/raw/raw.csv")
df = pd.read_csv(RAW_PATH, encoding="utf-8-sig")

required = {"row_id", "platform", "title", "comment"}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"Thiếu cột: {sorted(missing)}")

def normalize_for_review(value):
    if pd.isna(value):
        value = ""
    value = unicodedata.normalize("NFC", str(value)).casefold()
    return re.sub(r"\s+", " ", value).strip()

df["title_key"] = df["title"].map(normalize_for_review)
df["comment_key"] = df["comment"].map(normalize_for_review)

# Không chỉ dùng comment_key: cùng một câu có thể xuất hiện hợp lệ ở nhiều bài.
df["dedup_key"] = (
    df["platform"].fillna("").astype(str)
    + "\x1f" + df["title_key"]
    + "\x1f" + df["comment_key"]
)
```

### 9.2. Tạo danh sách ứng viên, không tự động xóa

Với raw hiện tại, cách an toàn là xuất nhóm trùng để kiểm tra:

```python
candidate_mask = df.duplicated("dedup_key", keep=False)

review = (
    df.loc[candidate_mask,
           ["row_id", "platform", "title", "comment", "dedup_key"]]
      .sort_values("dedup_key")
)
review.to_csv(
    "Preprocessing/data/raw_dedup_review.csv",
    index=False,
    encoding="utf-8-sig",
)
```

Không chạy `drop_duplicates` trực tiếp trên raw. Chỉ xóa một bản ghi khi có
định danh nguồn xác nhận đó là cùng comment, hoặc sau khi kiểm tra thủ công.
Nếu hai dòng giống nhau nhưng khác bài đăng, tác giả hoặc nguồn, giữ cả hai.

### 9.3. Near-duplicate

Không so sánh toàn bộ cặp comment bằng `O(n²)`. Chỉ tạo ứng viên trong cùng
`platform`, cùng `title_key` và nhóm độ dài gần nhau. Sau đó dùng Jaccard,
Levenshtein hoặc embedding để review. Không tự động xóa các câu khác emoji,
từ phủ định hoặc sắc thái cảm xúc.

Ví dụ ngưỡng gần trùng chỉ là ứng viên:

```text
phim này hay quá 😂
phim này hay quá 😒
```

Hai câu trên phải được giữ riêng vì emoji khác nhau có thể đổi nhãn cảm xúc.

### 9.4. Khử trùng đúng cách ở nguồn canonical

Nếu cần khử chắc chắn, phải làm trước bước merge, khi còn các trường:

```text
platform + comment_id
platform + post_id + comment_id
platform + video_id + comment_id
```

Sau khi merge thành raw 4 cột, các định danh này đã bị loại khỏi output. Do đó,
khử theo ID nên thực hiện trong dữ liệu nguồn hoặc trong bảng nội bộ trước khi
tạo `raw.csv`.

### 9.5. Quy trình áp dụng cho project

```text
Nguồn canonical có ID
→ khử trùng theo ID ở từng nguồn
→ merge thành raw.csv
→ tạo dedup_key giữ emoji và dấu câu
→ xuất raw_dedup_review.csv
→ kiểm tra thủ công các nhóm trùng
→ chỉ xóa bản ghi đã xác nhận là crawl trùng
```

`raw.csv` là bản snapshot dữ liệu, còn `raw_dedup_review.csv` là danh sách
ứng viên. Không ghi đè raw trước khi hoàn tất review.
