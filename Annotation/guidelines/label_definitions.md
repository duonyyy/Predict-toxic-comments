# Codebook nhãn DS108

## Taxonomy chính thức

Chỉ sử dụng bốn khái niệm sau:

1. `TOXIC`
2. `NON-TOXIC`
3. `EXPLICIT`
4. `IMPLICIT`

Quan hệ giữa các trường:

```text
toxicity: TOXIC / NON-TOXIC
expression_type: EXPLICIT / IMPLICIT / null
```

`expression_type` chỉ được gán khi `toxicity=TOXIC`. Không sử dụng thêm nhãn,
cảm xúc hoặc category khác.

## `TOXIC`

Bình luận có xúc phạm, lăng mạ, đe dọa, quấy rối, hạ nhục, phân biệt đối xử,
chế giễu hoặc công kích gây tổn thương/làm cuộc trò chuyện tiêu cực.

Không gán `TOXIC` chỉ vì bình luận có từ tục hoặc thể hiện bất đồng. Cần xét
chức năng của từ trong toàn câu.

## `NON-TOXIC`

Bình luận tích cực, trung tính, hỏi đáp hoặc phản biện ý tưởng/hành vi/sự việc
mà không công kích người hay nhóm người.

Từ tục chỉ dùng như khẩu ngữ/cảm thán, không hướng vào mục tiêu công kích, không
tự động làm bình luận thành `TOXIC`. Nếu chức năng không rõ, chuyển review.

## `EXPLICIT`

Nội dung độc hại được thể hiện trực tiếp và rõ ràng; người đọc không cần suy luận
nhiều để nhận ra hành vi xúc phạm, đe dọa hoặc công kích.

## `IMPLICIT`

Nội dung độc hại được thể hiện gián tiếp qua mỉa mai, ám chỉ, hàm ý, khuôn mẫu
hóa hoặc cách diễn đạt tinh vi; cần dựa vào ngữ cảnh văn bản để nhận ra.

## Trường hợp trích dẫn/thuật lại

Đánh giá mục tiêu giao tiếp của toàn comment:

- Trích dẫn để phản bác/lên án rõ ràng → `NON-TOXIC`.
- Trích dẫn được dùng để công kích hoặc thể hiện nội dung độc hại → `TOXIC` và
  chọn `EXPLICIT` hoặc `IMPLICIT`.
- Không xác định được mục tiêu giao tiếp → review.

## Trạng thái review

Review không phải nhãn. Nếu thiếu căn cứ hoặc có nhiều cách hiểu hợp lý:

```json
{
  "toxicity": null,
  "expression_type": null,
  "needs_review": true
}
```
