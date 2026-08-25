# Guideline gán nhãn bình luận DS108

## 1. Phạm vi

Đơn vị gán nhãn chỉ có trường `comment`. Đọc toàn bộ comment, không dò một từ
khóa riêng lẻ và không suy diễn người bị nhắm đến, nhóm xã hội, ý định hoặc ngữ
cảnh không xuất hiện trong comment.

Codebook duy nhất là `label_definitions.md`. Pipeline chỉ dùng bốn khái niệm:
`TOXIC`, `NON-TOXIC`, `EXPLICIT`, `IMPLICIT`.

## 2. Quy trình quyết định

### Bước 1 — Toxicity

- Không có công kích, đe dọa, hạ nhục hoặc nội dung gây tổn thương →
  `toxicity=NON-TOXIC`.
- Có công kích, đe dọa, hạ nhục hoặc nội dung gây tổn thương →
  `toxicity=TOXIC`.
- Không đủ căn cứ → `toxicity=null`, `needs_review=true`.

### Bước 2 — Expression type

Chỉ thực hiện khi `toxicity=TOXIC`:

- Nói trực tiếp, rõ ràng → `EXPLICIT`.
- Mỉa mai, ám chỉ, hàm ý hoặc khuôn mẫu hóa → `IMPLICIT`.

Không còn bước phân loại loại nội dung hoặc nguồn phát ngôn.

## 3. Trường hợp khó

- Từ tục không tự động là `TOXIC`; phải xét chức năng trong toàn câu.
- Phê bình ý tưởng, hành vi hoặc sự việc không phải công kích con người.
- Trích dẫn để phản bác/lên án → `NON-TOXIC`; nếu dùng để công kích → đánh giá
  theo nội dung độc hại.
- Emoji, teencode, tiếng Việt không dấu và code-mixing phải được đọc cùng toàn
  comment.
- Nếu vừa có cách hiểu độc hại vừa có cách hiểu không độc hại mà không đủ căn cứ,
  để null và đưa vào review.

## 4. Schema đầu ra

```json
{
  "toxicity": "TOXIC | NON-TOXIC | null",
  "expression_type": "EXPLICIT | IMPLICIT | null",
  "evidence": "một câu ngắn dựa trên comment",
  "needs_review": false,
  "review_reason": null
}
```

Ràng buộc:

- `NON-TOXIC` → `expression_type=null`.
- `TOXIC` → `expression_type` là `EXPLICIT` hoặc `IMPLICIT`.
- Chưa đủ căn cứ → các trường nhãn là null và `needs_review=true`.
- `needs_review`, `evidence`, `review_reason` là metadata, không phải nhãn.

## 5. Kiểm soát chất lượng

- Ít nhất hai annotator gán độc lập mẫu pilot.
- Tính IAA cho `toxicity` và `expression_type`.
- Adjudication các dòng bất đồng trước khi tạo gold label.
- LLM chỉ tiền dán nhãn, không tự quyết định gold label.
- Ghi `guideline_version`, `prompt_version`, model, thời điểm chạy và output gốc.
- Khi sửa guideline, tăng version và đánh giá lại mẫu bị ảnh hưởng.

## 6. Checklist annotator

- [ ] Chỉ đọc và gán nhãn trên `comment`.
- [ ] Đã xét toàn câu, không chỉ từ khóa.
- [ ] Đã phân biệt `TOXIC` và `NON-TOXIC`.
- [ ] Nếu `TOXIC`, đã chọn `EXPLICIT` hoặc `IMPLICIT`.
- [ ] Không suy diễn ngữ cảnh ngoài comment.
- [ ] Đã đánh dấu review khi chưa đủ căn cứ.
