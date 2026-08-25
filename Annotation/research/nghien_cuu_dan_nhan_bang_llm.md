# NGHIÊN CỨU PHƯƠNG PHÁP DÁN NHÃN DỮ LIỆU BẰNG LLM

## 1. Đặt vấn đề

Dán nhãn bình luận mạng xã hội quyết định chất lượng của bộ dữ liệu. Bình luận
thường ngắn, thiếu ngữ cảnh, có teencode, tiếng Việt không dấu, emoji, mỉa mai
và nhiều cách diễn đạt không chuẩn. Vì vậy, không nên dựa vào từ khóa hoặc giao
toàn bộ nhiệm vụ cho hệ thống tự động.

LLM có thể đọc guideline và đề xuất nhãn ở quy mô lớn, nhưng nhãn LLM không mặc
nhiên là nhãn đúng. LLM phù hợp nhất với vai trò tiền dán nhãn, phát hiện ca khó
và hỗ trợ kiểm tra; người kiểm duyệt vẫn quyết định nhãn cuối.

## 2. Codebook cố định

`guidelines/label_definitions.md` là nguồn chuẩn duy nhất. Hệ thống nhãn gồm:

1. `TOXIC` hoặc `NON-TOXIC`.
2. Nếu `TOXIC`: `EXPLICIT` hoặc `IMPLICIT`.

Không tạo thêm nhãn như cảm xúc, chủ đề, category hoặc nhãn mức độ khác trong
pipeline này.

Các trường `evidence`, `needs_review` và `review_reason` là metadata kiểm soát
chất lượng, không phải nhãn.

Định nghĩa chi tiết của bốn khái niệm được quản lý tại
`Annotation/guidelines/label_definitions.md`; prompt và guideline phải tham chiếu
cùng file này, không tự viết một taxonomy khác.

## 3. Mục tiêu nghiên cứu

1. Xây dựng quy trình dùng LLM để tiền dán nhãn theo codebook cố định.
2. Đo mức độ thống nhất giữa các annotator và giữa LLM với gold label.
3. Xác định các trường hợp khó: emoji, teencode, tiếng Việt không dấu, mỉa mai,
   trích dẫn, thuật lại và bình luận thiếu ngữ cảnh.
4. Đánh giá liệu LLM có giảm thời gian mà vẫn giữ được độ tin cậy hay không.

## 4. Phạm vi và tiền xử lý

Trước khi gửi dữ liệu cho LLM:

- giữ emoji, dấu câu, teencode và tiếng Việt không dấu khi chúng mang thông tin;
- loại bỏ hoặc ẩn danh tên người dùng, mention, email, số điện thoại và URL cá
  nhân không cần thiết;
- kiểm tra comment rỗng, HTML lỗi, duplicate và near-duplicate;
- lưu `row_id` ổn định để nối nhãn về dữ liệu gốc.

Không suy diễn người bị nhắm đến, nhóm xã hội hoặc ý định nếu thông tin đó không
có trong `comment` được cung cấp.

## 5. Vai trò của LLM

### 5.1. Tiền dán nhãn

LLM đề xuất nhãn theo codebook. Người nghiên cứu kiểm tra, sửa hoặc giữ
lại đề xuất này.

### 5.2. Đánh dấu trường hợp cần xem xét

LLM đặt `needs_review=true` khi thiếu ngữ cảnh, có nhiều cách hiểu hợp lý hoặc
không thể phân biệt chắc chắn giữa các nhãn. Đây là trạng thái kiểm duyệt, không
phải một nhãn mới.

### 5.3. Phát hiện lỗi nhãn

LLM có thể so sánh nhãn hiện có với nội dung để đề xuất bản ghi cần kiểm tra.
LLM không được tự động sửa gold label nếu chưa có quyết định của người.

## 6. Quy trình thực nghiệm

### Giai đoạn 1: Khảo sát dữ liệu

Lấy mẫu phân tầng theo nền tảng, độ dài, emoji, teencode, tiếng Việt không dấu,
dấu hiệu mỉa mai và nhóm duplicate. Không chỉ chọn các câu
dễ vì sẽ làm tăng giả tạo độ chính xác.

### Giai đoạn 2: Dán nhãn thủ công mẫu thí điểm

Ít nhất hai annotator đọc độc lập cùng một mẫu theo
`guidelines/label_definitions.md`.
Sau đó so sánh bất đồng, bổ sung ví dụ và làm rõ guideline. Mẫu tham chiếu của
con người không được tạo hoàn toàn bởi LLM.

### Giai đoạn 3: LLM tiền dán nhãn

LLM nhận prompt và `comment`, sau đó trả về JSON theo schema:

| Trường | Ý nghĩa |
|---|---|
| `row_id` | Mã bản ghi |
| `toxicity` | `TOXIC`, `NON-TOXIC` hoặc `null` khi chờ review |
| `expression_type` | `EXPLICIT`, `IMPLICIT` hoặc `null` |
| `evidence` | Căn cứ ngắn dựa trên nội dung |
| `needs_review` | Có cần người kiểm tra hay không |
| `review_reason` | Lý do cần kiểm tra |

Ràng buộc:

- `NON-TOXIC` luôn có hai trường nhãn phụ là `null`;
- `TOXIC` phải có một hình thức biểu đạt;
- trường hợp chưa đủ căn cứ để nhãn là `null` và `needs_review=true`;
- `null` chờ review không phải nhãn cuối.

### Giai đoạn 4: Kiểm tra và adjudication

Người kiểm duyệt đọc độc lập nội dung và nhãn LLM. Phân nhóm:

- trùng với annotator người;
- bất đồng với annotator người;
- thiếu ngữ cảnh hoặc cần hội đồng thống nhất.

Nhãn cuối do người có trách nhiệm quyết định theo codebook. Có thể dùng majority
voting khi thiết kế annotator phù hợp, nhưng phải lưu quyết định adjudication và
lý do đối với ca bất đồng.

### Giai đoạn 5: Mở rộng có kiểm soát

Sau pilot, dùng LLM tiền dán nhãn phần còn lại. Con người phải kiểm tra toàn bộ
ca `needs_review=true`, toàn bộ bất đồng và một mẫu ngẫu nhiên theo từng tầng
dữ liệu.

## 7. Thiết kế prompt

Prompt phải gồm:

1. Vai trò giới hạn của LLM.
2. Bốn khái niệm chính xác theo codebook.
3. Định nghĩa và điều kiện loại trừ của từng khái niệm.
4. Quy tắc cho từ tục, emoji, teencode, mỉa mai, phủ định và trích dẫn.
5. Quy tắc không suy diễn ngữ cảnh.
6. JSON schema bắt buộc.

Prompt không được dùng nhãn cảm xúc, nhãn category hoặc nhãn tự tạo khác như
một label chính thức.

## 8. Đánh giá chất lượng

### 8.1. Độ đồng thuận

- Cohen's Kappa cho hai annotator và một trường phân loại.
- Fleiss's Kappa hoặc Krippendorff's Alpha khi có nhiều annotator.
- Báo cáo raw agreement cùng Kappa/Alpha vì phân bố nhãn có thể mất cân bằng.
- Với bất đồng ở từng tầng, tính riêng `toxicity` và `expression_type`.

### 8.2. Chất lượng theo nhãn

Báo cáo precision, recall, F1-score, confusion matrix và phân bố nhãn. Không chỉ
dùng accuracy tổng thể.

### 8.3. Chất lượng theo nhóm dữ liệu

Tách kết quả theo nền tảng, độ dài comment, emoji, teencode, tiếng Việt không
dấu, duplicate và nhóm truy vấn thu thập nếu provenance có
đủ thông tin.

### 8.4. Tính ổn định

Chạy lại một mẫu trong cùng điều kiện để phát hiện nhãn thay đổi. Lưu model,
prompt version, guideline version, tham số, thời điểm, input hash và output gốc.
Không tự động chấp nhận những bản ghi không ổn định.

## 9. Rủi ro và kiểm soát

### 9.1. LLM quá tự tin

Buộc LLM dùng `needs_review` khi thiếu căn cứ; không biến câu trả lời rõ ràng
thành bằng chứng rằng nhãn đúng.

### 9.2. Thiên lệch ngôn ngữ và văn hóa

Dùng mẫu tiếng Việt thực tế, bao gồm tiếng lóng, cách chửi, mỉa mai và emoji.

### 9.3. Thiên lệch theo nền tảng

Giữ provenance và báo cáo theo nền tảng. Không kết luận cho toàn bộ dữ liệu từ
một nền tảng duy nhất.

### 9.4. Rò rỉ thông tin cá nhân

Ẩn danh trước khi gửi LLM; tuyệt đối không ghi API key vào log, checkpoint hoặc
output annotation.

### 9.5. Rò rỉ giữa các tập dữ liệu

Không chia duplicate, near-duplicate hoặc cùng nhóm bài đăng sang các split
khác nhau. Gold/test phải được adjudicate trước.

## 10. Quy trình khuyến nghị

`Dữ liệu raw + provenance`
`→ kiểm tra và ẩn danh`
`→ codebook cố định`
`→ pilot hai annotator`
`→ đo IAA và sửa guideline`
`→ LLM tiền dán nhãn`
`→ kiểm tra ca review/bất đồng`
`→ adjudication`
`→ gold dataset`
`→ AED và đánh giá phân bố`
`→ train/dev/test`

## 11. Câu hỏi nghiên cứu

1. LLM đồng thuận với annotator người ở mức nào trên từng tầng nhãn?
2. Nhóm dữ liệu nào làm LLM và annotator bất đồng nhiều nhất?
3. Emoji, teencode, mỉa mai và thiếu ngữ cảnh ảnh hưởng thế nào đến từng nhãn?
4. LLM hỗ trợ người có giảm thời gian nhưng vẫn giữ được chất lượng hay không?
5. Tỷ lệ `needs_review` có phản ánh đúng các trường hợp khó không?

## 12. Kết luận

LLM có thể giảm chi phí và thời gian dán nhãn, nhưng chỉ nên là trợ lý tiền dán
nhãn trong bộ dữ liệu này. Độ tin cậy phụ thuộc vào codebook thống nhất, mẫu
pilot đại diện, annotator độc lập, adjudication, kiểm tra theo nhóm dữ liệu và
khả năng tái lập. Nhãn cuối chỉ được sử dụng sau khi người kiểm duyệt xác nhận.
