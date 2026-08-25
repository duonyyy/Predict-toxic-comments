#  QUY TRÌNH TIỀN XỬ LÝ DỮ LIỆU

## 3. Quy trình tiền xử lý

Tiền xử lý là bước quan trọng nhằm chuyển dữ liệu thu thập từ nhiều nền tảng về
dạng nhất quán hơn, đồng thời giảm nhiễu mà không làm mất ý nghĩa của bình luận.
Quy trình được thực hiện tuần tự như sau:

**Bước 1 – Kiểm tra dữ liệu đầu vào.** Xác định các bản ghi bị rỗng, lỗi định
dạng, thiếu nội dung.

**Bước 2 – Loại bỏ thông tin nhận dạng cá nhân.** Xóa tên người dùng, số điện
thoại, email, đường dẫn cá nhân và các thông tin nhận dạng không cần thiết đối
với phần văn bản nghiên cứu.

**Bước 4 – Lọc nội dung không hữu ích.** Nhận diện và loại bỏ spam, quảng cáo,
nội dung hệ thống, chuỗi ký tự vô nghĩa hoặc nội dung không phải bình luận.
Việc lọc dựa trên ngữ cảnh, không loại bỏ chỉ vì bình luận ngắn.

**Bước 5 – Chuẩn hóa văn bản.** Chuẩn hóa Unicode, khoảng trắng và các lỗi định
dạng cơ bản. Không tự ý sửa nội dung làm thay đổi cách diễn đạt tự nhiên của
người dùng.

**Bước 7 – Kiểm tra trùng lặp.** Tạo các nhóm ứng viên dựa trên nền tảng, tiêu
đề và nội dung sau khi chuẩn hóa. Đây chỉ là bước phát hiện ứng viên, chưa đồng
nghĩa với việc xóa tự động.

**Bước 8 – Đánh giá trường hợp nghi ngờ.** Chỉ loại bỏ bản ghi khi có đủ căn cứ
cho thấy đó là kết quả thu thập lặp lại. Các bình luận giống nhau nhưng thuộc
bài đăng hoặc nền tảng khác nhau được giữ lại vì có thể là những quan sát độc
lập.



