# BÁO CÁO ĐỀ XUẤT QUY TRÌNH XỬ LÝ DỮ LIỆU TITLE VÀ COMMENT TRÊN MẠNG XÃ HỘI

## 1. Tổng quan

Dữ liệu được thu thập từ các nền tảng mạng xã hội gồm hai nhóm chính:

- **Title**: tiêu đề hoặc nội dung chính của bài đăng.
- **Comment**: nội dung bình luận của người dùng.

Sau khi crawl, dữ liệu thường chưa thể sử dụng trực tiếp vì có thể chứa bản ghi trùng lặp, dữ liệu rỗng, spam, lỗi mã hóa, ngôn ngữ hỗn hợp, từ viết tắt, emoji, URL và thông tin cá nhân.

Báo cáo này đề xuất một quy trình xử lý từ dữ liệu thô đến dữ liệu sẵn sàng cho phân tích, xây dựng mô hình AI và dashboard.

---

## 2. Mục tiêu xử lý dữ liệu

Trước khi triển khai, cần xác định mục tiêu sử dụng dữ liệu. Một số mục tiêu phổ biến gồm:

- Phân tích cảm xúc tích cực, tiêu cực và trung lập.
- Xác định các chủ đề được thảo luận nhiều.
- Phát hiện bình luận spam, quảng cáo hoặc tài khoản có hành vi bất thường.
- Tìm từ khóa, thương hiệu, sản phẩm hoặc tính năng được nhắc đến.
- Theo dõi xu hướng thảo luận theo thời gian.
- So sánh phản ứng của người dùng giữa các nền tảng.
- Xác định ý định của người dùng như khiếu nại, hỏi thông tin hoặc có nhu cầu mua hàng.
- Xây dựng tập dữ liệu huấn luyện cho mô hình machine learning hoặc AI.

Mỗi mục tiêu có thể yêu cầu cách làm sạch, gắn nhãn và đánh giá khác nhau.

---

## 3. Chuẩn hóa cấu trúc dữ liệu

Dữ liệu từ nhiều nền tảng nên được chuyển về một cấu trúc thống nhất.

| Tên trường | Mô tả |
|---|---|
| `platform` | Nền tảng thu thập dữ liệu |
| `post_id` | Mã định danh bài đăng |
| `comment_id` | Mã định danh bình luận |
| `parent_comment_id` | Mã bình luận cha nếu là phản hồi |
| `title` | Tiêu đề hoặc nội dung chính của bài đăng |
| `comment` | Nội dung bình luận |
| `created_at` | Thời gian đăng |
| `crawl_time` | Thời gian thu thập |
| `author_id` | Mã người dùng đã được ẩn danh |
| `like_count` | Số lượt thích |
| `reply_count` | Số lượt phản hồi |
| `url` | Đường dẫn nguồn |
| `language` | Ngôn ngữ của nội dung |

Không nên lưu trực tiếp tên thật, số điện thoại, email hoặc thông tin định danh nếu không cần thiết. Có thể hash `author_id` để phục vụ phân tích hành vi mà vẫn giảm rủi ro về quyền riêng tư.

---

## 4. Kiểm tra chất lượng dữ liệu

Trước khi làm sạch, cần thực hiện phân tích tổng quan để đánh giá chất lượng dữ liệu.

Các chỉ số nên thống kê:

- Tổng số bài đăng.
- Tổng số bình luận.
- Số lượng dữ liệu theo từng nền tảng.
- Tỷ lệ dữ liệu rỗng.
- Số bản ghi trùng lặp.
- Độ dài trung bình của title và comment.
- Phân bố dữ liệu theo ngày, giờ hoặc tuần.
- Tỷ lệ ngôn ngữ.
- Số lượng URL, hashtag, mention và emoji.
- Các khoảng thời gian dữ liệu tăng hoặc giảm bất thường.

Bước này giúp phát hiện các vấn đề của crawler như:

- Crawl lặp dữ liệu.
- Mất dữ liệu trong một khoảng thời gian.
- Sai định dạng ngày giờ.
- Một nền tảng chiếm tỷ trọng quá lớn.
- Nội dung bị lỗi mã hóa ký tự.

---

## 5. Loại bỏ dữ liệu lỗi và trùng lặp

### 5.1. Dữ liệu cần loại bỏ

- Comment hoặc title rỗng.
- Nội dung chỉ chứa khoảng trắng.
- Bản ghi không có mã định danh cần thiết.
- Nội dung hệ thống như “Comment không khả dụng”.
- HTML hoặc dữ liệu lỗi do crawler.
- Bản ghi trùng `comment_id`.
- Bản ghi bị crawler lấy lại nhiều lần.

### 5.2. Phát hiện trùng lặp

Có thể chia thành hai loại:

**Trùng tuyệt đối**

Hai bản ghi có toàn bộ nội dung giống nhau.

**Trùng gần giống**

Ví dụ:

```text
Sản phẩm này rất tốt
Sản phẩm này rất tốt!!!
Sản phẩm này rất tốt ❤
```

Để phát hiện trùng gần giống, có thể:

1. Chuyển nội dung về chữ thường.
2. Chuẩn hóa khoảng trắng.
3. So sánh dấu câu và các thành phần ngữ nghĩa.
4. Giữ nguyên emoji khi tạo khóa so sánh.
5. Tạo khóa so sánh từ nội dung đã chuẩn hóa.
6. Kiểm tra ngữ cảnh bài đăng trước khi quyết định xử lý.

Không nên xóa trực tiếp mọi bản ghi trùng gần giống. Cần xem xét trường hợp nhiều người dùng thực sự đăng cùng một nội dung hoặc có hành vi spam.

---

## 6. Làm sạch và chuẩn hóa văn bản

Nên giữ hai phiên bản của dữ liệu:

- `raw_text`: nội dung gốc.
- `clean_text`: nội dung đã được xử lý.

Các bước làm sạch phổ biến:

1. Chuẩn hóa Unicode.
2. Loại bỏ HTML.
3. Chuẩn hóa khoảng trắng.
4. Chuẩn hóa xuống dòng.
5. Xóa URL, số điện thoại, email hoặc thông tin nhận dạng không cần thiết.
6. Xóa tên người được tag hoặc mention dạng `@tên_người_dùng` ở đầu bình luận
   khi xác định đó là phần giao diện, không phải nội dung người dùng muốn truyền
   đạt.
7. Giữ hashtag nếu nó còn có ý nghĩa đối với nội dung.
8. Không tự ý sửa chữ hoa, chữ thường, từ viết tắt hoặc tiếng lóng.
9. Không tự ý sửa ký tự lặp nếu việc sửa có thể làm thay đổi sắc thái.
10. Giữ nguyên emoji trong nội dung sau xử lý.

Ví dụ làm sạch và bảo toàn ngữ nghĩa:

```text
"  Sản   phẩm   này   tốt!!!  " → "Sản phẩm này tốt!!!"
"Liên hệ 0900000000 để mua hàng" → loại bỏ nếu xác định là quảng cáo/spam
"Món này vui quá 😂👍" → "Món này vui quá 😂👍"
"✅" → "✅"
"ko mua đâu 😭" → "ko mua đâu 😭"
```

Trong các ví dụ trên, emoji không bị xóa, thay thế hoặc chuyển thành nhãn văn
bản. Các emoji cần được bảo toàn gồm: ✅, ❤, 😂, 😭, 🥰, 🤣 và 👍.

### 6.1. Ví dụ tổng hợp theo quy trình

Bảng dưới đây minh họa cách xử lý một số trường hợp thường gặp trong dữ liệu
thực tế:

| Trường hợp | Dữ liệu trước xử lý | Kết quả xử lý | Nguyên tắc áp dụng |
|---|---|---|---|
| Khoảng trắng thừa | `  Món này ngon   quá  ` | `Món này ngon quá` | Chuẩn hóa khoảng trắng |
| Emoji | `Đẹp quá 😂👍` | `Đẹp quá 😂👍` | Giữ nguyên emoji, không biến đổi |
| Bình luận chỉ có emoji | `😭` | `😭` | Giữ vì vẫn có thể biểu đạt cảm xúc |
| Thông tin cá nhân | `Gửi vào mail abc@example.com nhé` | `Gửi vào mail nhé` | Xóa email không cần thiết |
| Quảng cáo | `Mua hàng giá rẻ, gọi 0900000000` | Loại bỏ | Loại bỏ nếu xác định là spam/quảng cáo |
| Nội dung hệ thống | `Comment không khả dụng` | Loại bỏ | Không phải nội dung bình luận |
| Gần trùng | `Sản phẩm này rất tốt` và `Sản phẩm này rất tốt!!!` | Đưa vào nhóm cần xem xét | Không xóa tự động nếu chưa đủ căn cứ |

Các ví dụ trên chỉ minh họa nguyên tắc. Những trường hợp không chắc chắn cần
được giữ lại hoặc đưa vào nhóm xem xét, thay vì loại bỏ máy móc.

---

## 7. Phát hiện ngôn ngữ

Dữ liệu mạng xã hội có thể gồm:

- Tiếng Việt có dấu.
- Tiếng Việt không dấu.
- Tiếng Anh.
- Nội dung trộn tiếng Việt và tiếng Anh.
- Nội dung chỉ có emoji hoặc ký hiệu.

Nên bổ sung cột:

```text
language = vi / en / mixed / unknown
```

Có thể xử lý riêng từng nhóm ngôn ngữ hoặc sử dụng mô hình đa ngôn ngữ.

---

## 8. Phát hiện spam và nội dung không hữu ích

### 8.1. Dấu hiệu spam phổ biến

- Một nội dung được lặp lại trên nhiều bài đăng.
- Chứa nhiều số điện thoại hoặc URL.
- Nội dung quảng cáo hoặc bán hàng hàng loạt.
- Một tài khoản bình luận với tần suất bất thường.
- Comment chỉ gồm tag người dùng.
- Nội dung quá ngắn như `.`, `up`, `ib`.
- Chuỗi ký tự vô nghĩa.
- Nội dung copy-paste hàng loạt.

### 8.2. Cấu trúc kết quả đề xuất

Thay vì xóa ngay, nên tạo các trường:

```text
spam_score: 0.0 - 1.0
is_spam: true / false
spam_reason: duplicate / phone_number / repeated_text / advertising
```

Cách làm này giúp điều chỉnh ngưỡng lọc và kiểm tra lại dữ liệu sau này.

---

## 9. Tách đơn vị phân tích

### 9.1. Cấp bình luận

Mỗi comment là một bản ghi.

Phù hợp cho:

- Phân tích cảm xúc.
- Phân loại ý định.
- Phát hiện spam.
- Trích xuất thực thể.

### 9.2. Cấp bài đăng

Gộp các bình luận theo `post_id`.

Có thể tính:

- Số lượng bình luận.
- Tỷ lệ cảm xúc tích cực và tiêu cực.
- Chủ đề chính.
- Tỷ lệ spam.
- Mức độ tương tác.
- Các bình luận đại diện.

### 9.3. Cấp người dùng đã ẩn danh

Có thể dùng để:

- Phát hiện nội dung lặp.
- Phát hiện tài khoản có hành vi giống bot.
- Phân tích mức độ hoạt động.

Việc phân tích người dùng cần tuân thủ các yêu cầu về quyền riêng tư và bảo vệ dữ liệu cá nhân.

### 9.4. Cấp thời gian

Gộp dữ liệu theo:

- Giờ.
- Ngày.
- Tuần.
- Tháng.

Mục tiêu là phát hiện xu hướng, sự kiện bất thường hoặc biến động về cảm xúc.

---

## 10. Trích xuất đặc trưng cơ bản

Trước khi sử dụng mô hình AI phức tạp, nên tạo các đặc trưng đơn giản:

```text
text_length
word_count
emoji_count
has_url
has_phone
has_hashtag
has_mention
uppercase_ratio
exclamation_count
question_count
like_count
reply_count
```

Các đặc trưng này có thể sử dụng để:

- Phát hiện spam.
- Phân tích tương tác.
- Xây dựng mô hình machine learning.
- Tạo báo cáo thống kê.

---

## 11. Phân tích nội dung

### 11.1. Phân tích cảm xúc

Đầu ra đề xuất:

```text
sentiment_label: positive / negative / neutral
sentiment_score: -1.0 - 1.0
sentiment_confidence: 0.0 - 1.0
```

Các trường hợp cần chú ý:

- Câu phủ định.
- Câu mỉa mai.
- Emoji.
- Từ lóng.
- Nội dung vừa tích cực vừa tiêu cực.
- Bình luận phụ thuộc vào ngữ cảnh bài viết.

### 11.2. Phân loại chủ đề

Ví dụ với dữ liệu sản phẩm:

```text
price
quality
delivery
customer_service
design
warranty
promotion
other
```

Một comment có thể chứa nhiều chủ đề, vì vậy bài toán multi-label thường phù hợp hơn phân loại một nhãn duy nhất.

### 11.3. Phân loại ý định

Các nhãn tham khảo:

```text
asking_question
complaint
purchase_intent
request_support
recommendation
advertisement
general_discussion
```

### 11.4. Trích xuất thực thể

Có thể trích xuất:

- Tên thương hiệu.
- Tên sản phẩm.
- Địa điểm.
- Giá tiền.
- Tính năng.
- Lỗi sản phẩm.
- Đối thủ cạnh tranh.
- Chương trình khuyến mại.

---

## 12. Khám phá chủ đề chưa biết trước

Khi chưa có bộ nhãn chủ đề, có thể sử dụng quy trình:

```text
Clean text
→ Embedding
→ Clustering
→ Keyword extraction
→ Topic naming
→ Manual review
```

Các bước triển khai:

1. Chuyển comment thành vector embedding.
2. Gom cụm các comment có nội dung tương tự.
3. Lấy các comment đại diện của mỗi cụm.
4. Trích xuất từ khóa.
5. Đặt tên cho từng cụm.
6. Kiểm tra thủ công.
7. Xây dựng bộ nhãn chính thức.

Word cloud chỉ nên dùng để minh họa, không nên xem là phương pháp chính để xác định chủ đề vì nó không phản ánh đầy đủ ngữ cảnh.

---

## 13. Gắn nhãn dữ liệu mẫu

Trước khi xử lý toàn bộ dữ liệu, nên lấy một tập mẫu và gắn nhãn thủ công.

Cấu trúc tham khảo:

```text
comment
sentiment
topic
intent
spam
confidence
annotator
```

Cần xây dựng hướng dẫn gắn nhãn rõ ràng:

- Khi nào một comment là tích cực?
- Khi nào là tiêu cực?
- Khi nào là trung lập?
- Comment vừa khen vừa chê được xử lý thế nào?
- Comment mỉa mai được gắn nhãn ra sao?
- Comment chỉ có emoji được xử lý như thế nào?
- Comment quảng cáo có được giữ lại hay không?

Nếu có nhiều người gắn nhãn, nên đo mức độ đồng thuận giữa các annotator.

---

## 14. Đánh giá mô hình

Không nên chỉ sử dụng accuracy, đặc biệt khi dữ liệu mất cân bằng.

Các chỉ số nên theo dõi:

- Precision.
- Recall.
- F1-score.
- Confusion matrix.
- Kết quả theo từng nền tảng.
- Kết quả theo từng ngôn ngữ.
- Kết quả theo comment ngắn và comment dài.
- Tỷ lệ dự đoán có độ tin cậy thấp.

Ví dụ, nếu 90% dữ liệu là trung lập, một mô hình luôn dự đoán trung lập vẫn có accuracy cao nhưng không mang lại nhiều giá trị.

---

## 15. Lưu trữ dữ liệu theo từng tầng

Không nên xử lý trực tiếp trên dữ liệu gốc. Nên chia thành các tầng:

```text
raw/
  facebook/
  youtube/
  tiktok/

processed/
  cleaned_comments.parquet

features/
  comment_features.parquet

predictions/
  sentiment_predictions.parquet
  topic_predictions.parquet

reports/
  daily_summary.csv
```

Định dạng Parquet thường phù hợp hơn CSV khi dữ liệu lớn vì:

- Tốc độ đọc ghi nhanh hơn.
- Dung lượng nhỏ hơn.
- Giữ được kiểu dữ liệu.
- Phù hợp cho xử lý dữ liệu theo lô.

Mỗi kết quả dự đoán nên có các trường:

```text
model_name
model_version
prediction_time
confidence_score
processing_version
```

Điều này giúp so sánh các phiên bản mô hình và tái tạo kết quả.

---

## 16. Dashboard và báo cáo

Dashboard ban đầu có thể gồm:

- Tổng số bài đăng và bình luận.
- Số lượng dữ liệu theo nền tảng.
- Sentiment theo ngày.
- Tỷ lệ sentiment theo nền tảng.
- Các chủ đề được nhắc đến nhiều nhất.
- Chủ đề có tỷ lệ tiêu cực cao.
- Bài đăng có mức tương tác cao.
- Bình luận tiêu biểu.
- Tỷ lệ spam.
- Từ khóa có tốc độ tăng nhanh.
- So sánh phản ứng giữa các nền tảng.

---

## 17. Pipeline tối thiểu đề xuất

```text
Dữ liệu crawl
→ Chuẩn hóa schema
→ Kiểm tra chất lượng
→ Loại bỏ dữ liệu lỗi
→ Loại bỏ trùng lặp
→ Làm sạch văn bản
→ Phát hiện ngôn ngữ
→ Phát hiện spam
→ Trích xuất đặc trưng
→ Phân tích cảm xúc
→ Phân loại hoặc khám phá chủ đề
→ Kiểm tra thủ công
→ Lưu kết quả
→ Xây dựng dashboard
```

---

## 18. Cấu trúc dữ liệu đầu ra đề xuất

```text
platform
post_id
comment_id
parent_comment_id
raw_text
clean_text
language
is_duplicate
spam_score
is_spam
spam_reason
sentiment
sentiment_confidence
topics
intent
created_at
like_count
reply_count
model_version
processing_version
```

---

## 19. Thứ tự triển khai thực tế

Có thể chia quá trình triển khai thành bốn giai đoạn.

### Giai đoạn 1: Làm sạch và kiểm tra dữ liệu

- Chuẩn hóa schema.
- Xử lý dữ liệu rỗng.
- Loại bỏ bản ghi trùng.
- Chuẩn hóa văn bản.
- Thống kê chất lượng dữ liệu.

### Giai đoạn 2: Phân tích cơ bản

- Phát hiện ngôn ngữ.
- Thống kê từ khóa.
- Phân tích độ dài nội dung.
- Xây dựng quy tắc phát hiện spam.
- Phân tích xu hướng theo thời gian.

### Giai đoạn 3: Phân tích bằng AI

- Phân tích cảm xúc.
- Phân loại ý định.
- Phân loại chủ đề.
- Trích xuất thực thể.
- Gom cụm chủ đề chưa biết trước.

### Giai đoạn 4: Báo cáo và vận hành

- Xây dựng dashboard.
- Theo dõi chất lượng mô hình.
- Quản lý phiên bản dữ liệu.
- Quản lý phiên bản pipeline.
- Thiết lập lịch xử lý định kỳ.

---

## 20. Kết luận

Quy trình xử lý dữ liệu mạng xã hội nên bắt đầu từ việc xác định mục tiêu, chuẩn hóa cấu trúc và kiểm tra chất lượng dữ liệu trước khi áp dụng các mô hình AI.

Ba nguyên tắc quan trọng nhất gồm:

1. **Luôn giữ nguyên dữ liệu raw.**
2. **Không xóa dữ liệu trước khi có quy tắc và khả năng kiểm tra lại.**
3. **Ghi lại phiên bản của pipeline, dữ liệu và mô hình.**

Một phiên bản đầu tiên không cần quá phức tạp. Có thể bắt đầu từ làm sạch dữ liệu, loại bỏ trùng lặp, phát hiện spam, phân tích cảm xúc và thống kê chủ đề; sau đó mở rộng dần sang các mô hình nâng cao.
