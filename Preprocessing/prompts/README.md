# Hướng dẫn sử dụng prompt sinh dữ liệu

## File chính

Sử dụng duy nhất:

`PROMPT_FINAL.md`

Các prompt cũ nằm trong `archive` chỉ để đối chiếu, không gửi đồng thời cho ChatGPT.

## File nên gửi cho ChatGPT

1. `PROMPT_FINAL.md`.
2. Một mẫu `raw.csv` đã ẩn danh và phân tầng theo platform.
3. Tùy chọn: `chuanhoa/teencode_researched_2026.csv` nếu cần mở rộng vốn slang.

Không gửi đồng thời cả ba CSV teencode, file Excel và `teencode.txt`, vì chúng trùng nhiều nội dung và làm tăng nhiễu ngữ cảnh.

`teencode.txt` là từ điển legacy có nhiều ánh xạ phụ thuộc ngữ cảnh. Các file trong `chuanhoa` phục vụ chuẩn hóa và kiểm định bên ngoài, không phải prompt độc lập.

## Cách chạy mỗi batch

Trước khi gửi prompt, bắt buộc thay:

- `[SỐ_LƯỢNG]`.
- `[START_ROW_ID]` nếu không muốn bắt đầu từ 1.

Có thể thay thêm:

- `[MAX_COMMENTS_PER_TITLE]`.
- `[DANH_SÁCH_TITLE_HƯ_CẤU]`.
- Năm quota platform.

Nên tạo 20–100 dòng mỗi batch. Batch tiếp theo phải tăng `START_ROW_ID` để không trùng ID.

Lưu mỗi batch vào file riêng, ví dụ:

`synthetic_toxic_batch_001.csv`

Không gộp dữ liệu tổng hợp vào `raw.csv` trước khi lưu manifest bên ngoài chứa tối thiểu:

`file_name,source,label,prompt_version,created_at`

## Kiểm định sau khi sinh

Không dựa hoàn toàn vào phần “kiểm tra âm thầm” của mô hình. Dùng code để kiểm tra:

- Số dòng và schema bốn cột.
- `row_id` liên tục, không trùng.
- Quota platform.
- CSV parse được.
- Trùng chính xác và gần trùng.
- N-gram trùng với `raw.csv`.
- Tên hoặc tài khoản thật.
- Lỗi mã hóa.
- Phân bố độ dài, từ tục và slang.

Dữ liệu sinh bởi prompt này chỉ là lớp độc hại tổng hợp. Tập huấn luyện hoàn chỉnh vẫn cần dữ liệu trung tính, phê bình không độc hại, độc hại không từ tục và câu có từ tục nhưng không công kích.
