# Bộ dữ liệu chuẩn hóa Teencode tiếng Việt 2026

## Đây là gì?

Thư mục này chứa **bộ từ điển chuẩn hóa teencode/tiếng lóng tiếng Việt** phục vụ
tiền xử lý văn bản và các bài toán NLP như phân loại cảm xúc, phát hiện tin giả,
phát hiện nội dung độc hại hoặc tìm kiếm văn bản.

Mỗi bản ghi ánh xạ một từ/cụm từ không chuẩn (`token`) sang dạng tiếng Việt được
chuẩn hóa (`normalized`), ví dụ:

| Token | Dạng chuẩn hóa | Xử lý đề xuất |
|---|---|---|
| `lun` | `luôn` | Có thể thay tự động |
| `gòi` | `rồi` | Có thể thay tự động |
| `nma` | `nhưng mà` | Có thể thay tự động |
| `t` | `tôi` | Không thay tự động vì có thể là `tao`, `tớ`, `tui`,... |
| `m` | `mày` | Không thay tự động vì phụ thuộc ngữ cảnh |

Đây là **dữ liệu**, không phải một chương trình có thể chạy độc lập.

## Thành phần thư mục

| File | Nội dung | Số bản ghi |
|---|---|---:|
| `teencode_researched_2026.xlsx` | Workbook đầy đủ để đọc, lọc và kiểm tra bằng Excel | 1.450 |
| `teencode_researched_2026.csv` | Toàn bộ từ điển ở định dạng CSV | 1.450 |
| `teencode_safe_auto_2026.csv` | Tập con được đánh dấu có thể thay tự động | 544 |
| `teencode_review_queue_2026.csv` | Tập cần giữ nguyên hoặc duyệt theo ngữ cảnh | 906 |

Hai tập con tạo thành đúng toàn bộ tập dữ liệu:

```text
544 mục Safe_Auto + 906 mục Review_Queue = 1.450 mục Dictionary
```

Tỷ lệ tương ứng là khoảng **37,5% có thể thay tự động** và **62,5% cần duyệt**.
Không phát hiện token trùng trong bản dữ liệu tổng.

### Các sheet trong file Excel

| Sheet | Vai trò |
|---|---|
| `Summary` | Thống kê và nguyên tắc sử dụng |
| `Dictionary` | Toàn bộ 1.450 mục |
| `Safe_Auto` | 544 mục có `auto_replace = yes` |
| `Review_Queue` | 906 mục có `auto_replace = no` |
| `Sources` | Nguồn, vai trò và ghi chú giấy phép |

Các file CSV dùng mã hóa **UTF-8 có BOM**, phù hợp để mở bằng Excel và đọc bằng
phần lớn thư viện xử lý dữ liệu.

## Cấu trúc một bản ghi

| Cột | Ý nghĩa |
|---|---|
| `token` | Từ hoặc cụm từ gốc cần nhận diện |
| `normalized` | Dạng tiếng Việt chuẩn hóa được đề xuất |
| `category` | Nhóm dữ liệu, ví dụ viết tắt, biến thể chính tả hoặc từ xu hướng |
| `period` | Thời kỳ hoặc nguồn thời gian của mục từ |
| `is_ambiguous` | `yes` nếu ánh xạ có thể có nhiều nghĩa |
| `alternative_meanings` | Các nghĩa khác, phân tách bằng dấu `|` |
| `recommendation` | Khuyến nghị xử lý mục từ |
| `notes` | Ghi chú về cách suy ra hoặc giới hạn của ánh xạ |
| `auto_replace` | `yes` nếu được phép thay tự động, ngược lại là `no` |
| `evidence_count` | Số lần ánh xạ được quan sát trong dữ liệu nguồn |
| `confidence` | Điểm tin cậy được lưu trong dữ liệu, từ 0 đến 1 |
| `status` | Trạng thái kiểm chứng hoặc lý do cần duyệt |
| `source` | Nguồn của mục từ |
| `example` | Ví dụ chứa token trong ngữ cảnh thực tế |

### Các nhóm dữ liệu

| `category` | Số mục | Diễn giải |
|---|---:|---|
| `abbreviation_or_variant` | 745 | Viết tắt hoặc biến thể cách viết |
| `legacy_lexicon` | 472 | Mục từ kế thừa từ từ điển cũ |
| `orthographic_variant` | 142 | Biến thể chính tả |
| `trend_or_codeswitch` | 38 | Tiếng lóng xu hướng hoặc trộn ngôn ngữ |
| `phrase_candidate` | 27 | Cụm từ ứng viên, cần xét ngữ cảnh |
| `trend_phrase` | 26 | Cụm từ xu hướng |

## Cách sử dụng khuyến nghị

Quy trình an toàn:

1. Luôn lưu văn bản gốc trong `content_original`.
2. Chỉ dùng file `teencode_safe_auto_2026.csv` để thay tự động.
3. Ghi kết quả vào trường riêng như `content_normalized`.
4. Đưa các mục trong `teencode_review_queue_2026.csv` vào bước xử lý theo ngữ
   cảnh hoặc duyệt thủ công.
5. Đánh giá tác động của chuẩn hóa trên tập kiểm thử của chính bài toán trước khi
   dùng trong production.

Ví dụ Python tối giản:

```python
import csv
import re


def load_safe_mapping(csv_path: str) -> dict[str, str]:
    with open(csv_path, encoding="utf-8-sig", newline="") as file:
        rows = csv.DictReader(file)
        return {
            row["token"]: row["normalized"]
            for row in rows
            if row["auto_replace"] == "yes"
        }


def normalize_text(text: str, mapping: dict[str, str]) -> str:
    # Ưu tiên cụm dài trước để tránh thay một phần của cụm từ.
    tokens = sorted(mapping, key=len, reverse=True)
    if not tokens:
        return text

    pattern = re.compile(
        r"(?<!\w)(" + "|".join(map(re.escape, tokens)) + r")(?!\w)",
        flags=re.IGNORECASE,
    )
    return pattern.sub(lambda match: mapping.get(match.group(0).lower(), match.group(0)), text)


safe_mapping = load_safe_mapping("teencode_safe_auto_2026.csv")
content_original = "gòi nma tui chưa mún đi lun"
content_normalized = normalize_text(content_original, safe_mapping)

print(content_original)
print(content_normalized)
```

Đoạn mã trên chỉ là ví dụ nền. Nếu cần giữ nguyên kiểu viết hoa, xử lý Unicode
NFC/NFD hoặc tokenization chuyên biệt cho tiếng Việt thì phải bổ sung logic.

## Nguồn và phương pháp

Theo metadata trong workbook, bộ dữ liệu được xây dựng bằng cách:

- căn chỉnh token từ **10.467 cặp câu original/normalized của ViLexNorm**;
- đối chiếu các từ điển teencode cũ;
- bổ sung và gắn cờ các từ/cụm từ xu hướng năm 2025;
- tách riêng ánh xạ có bằng chứng lặp lại, ít đa nghĩa khỏi các mục phụ thuộc
  ngữ cảnh.

Các nguồn được ghi trong sheet `Sources`, gồm ViLexNorm, ViSoLex,
Small-LexNormViHSD, danh sách teencode ABSA-VLSP2018 và một số bài viết mô tả
tiếng lóng/xu hướng năm 2025. Khi phân phối lại hoặc dùng thương mại, cần kiểm
tra điều khoản của từng nguồn gốc; không nên suy ra rằng toàn bộ workbook dùng
chung một giấy phép.

## Giới hạn và cảnh báo

- `auto_replace = yes` là **nhãn khuyến nghị của bộ dữ liệu**, không phải bảo đảm
  rằng phép thay luôn đúng trong mọi miền dữ liệu.
- `confidence` là điểm được suy ra từ bằng chứng trong dữ liệu nguồn; không nên
  mặc định coi nó là xác suất đã được hiệu chỉnh.
- Có 312 mục thiếu `evidence_count`, `confidence` và `example`; phần lớn các mục
  này cần được xem là chưa có đủ bằng chứng định lượng.
- Có 472 mục không có `period`, nên không thể xác định độ mới chỉ từ cột này.
- Token một ký tự, từ đa nghĩa, meme, cụm từ xu hướng và code-switch đặc biệt dễ
  bị chuẩn hóa sai nếu không dùng ngữ cảnh.
- Một số mục chứa từ tục hoặc nội dung nhạy cảm vì dữ liệu dùng để nhận diện
  ngôn ngữ mạng. Cần kiểm soát quyền truy cập và cách hiển thị nếu dùng trong sản
  phẩm hướng tới người dùng.
- Việc chuẩn hóa có thể làm mất tín hiệu quan trọng cho phân tích phong cách,
  phương ngữ, mỉa mai, nhóm tuổi hoặc phát hiện nội dung độc hại. Nên giữ cả bản
  gốc và bản chuẩn hóa.
- Khi thay thế, phải xét ranh giới từ và ưu tiên cụm dài trước; không dùng
  `str.replace()` trực tiếp trên toàn bộ chuỗi vì có thể thay nhầm bên trong một
  từ khác.

## Kết luận

Bộ dữ liệu này phù hợp làm **lớp hỗ trợ chuẩn hóa văn bản tiếng Việt không chuẩn**.
Giá trị chính của nó không chỉ nằm ở cặp `token → normalized`, mà còn ở việc tách
rõ mục có thể tự động hóa và mục phải xử lý theo ngữ cảnh. Cách dùng an toàn nhất
là coi nó như một nguồn ứng viên có metadata, không phải một bộ luật thay thế tuyệt
đối.
