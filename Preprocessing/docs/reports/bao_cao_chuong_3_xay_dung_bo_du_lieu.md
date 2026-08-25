# CHƯƠNG 3. XÂY DỰNG VÀ TIỀN XỬ LÝ BỘ DỮ LIỆU BÌNH LUẬN MẠNG XÃ HỘI

## 3.1. Mục tiêu xây dựng bộ dữ liệu

Mục tiêu của chương này là xây dựng một bộ dữ liệu văn bản tiếng Việt được
thu thập từ nhiều nền tảng mạng xã hội, sau đó đưa về cấu trúc thống nhất và
tiền xử lý theo các nguyên tắc phù hợp với ngữ liệu mạng xã hội.

Quy trình được thiết kế theo ba yêu cầu chính:

1. Giữ lại thông tin ngữ nghĩa và sắc thái biểu cảm của bình luận.
2. Loại bỏ dữ liệu lỗi, thông tin nhận dạng và nội dung rõ ràng không hữu ích.
3. Bảo đảm dữ liệu có thể kiểm tra, đối chiếu và sử dụng cho các nghiên cứu
   tiếp theo.

Khác với văn bản viết theo chuẩn học thuật, bình luận mạng xã hội thường có
teencode, lỗi chính tả, câu rút gọn, tiếng Việt không dấu, emoji, ký hiệu và
cách diễn đạt phụ thuộc vào ngữ cảnh. Vì vậy, việc tiền xử lý không nhằm biến
đổi văn bản thành một dạng hoàn toàn chuẩn hóa, mà nhằm giảm nhiễu nhưng vẫn
bảo toàn thông tin quan trọng.

## 3.2. Đơn vị dữ liệu và phạm vi nghiên cứu

Đơn vị phân tích chính của bộ dữ liệu là bình luận. Mỗi bình luận được xem là
một đoạn văn bản có thể chứa quan điểm, cảm xúc, thông tin trao đổi hoặc hành
vi giao tiếp của người dùng.

Trong dữ liệu mạng xã hội, `title` đại diện cho tiêu đề hoặc nội dung chính
của bài đăng, còn `comment` là phần phản hồi của người dùng. Hai trường này
được giữ trong bảng raw để hỗ trợ việc xem xét ngữ cảnh khi cần thiết.

Bảng raw sau bước merge gồm bốn trường:

| Trường | Ý nghĩa |
|---|---|
| `row_id` | Số thứ tự của bản ghi trong snapshot raw |
| `platform` | Nền tảng phát sinh dữ liệu |
| `title` | Tiêu đề hoặc nội dung chính của bài đăng |
| `comment` | Nội dung bình luận hoặc phản hồi |

Các thông tin như tên người dùng, URL cá nhân, email, số điện thoại và tên
người được tag không thuộc phần văn bản dùng cho nghiên cứu.

## 3.3. Nguồn và phương pháp thu thập dữ liệu

Dữ liệu được tổng hợp từ nhiều nguồn nhằm tăng tính đa dạng về chủ đề, phong
cách diễn đạt và hành vi giao tiếp. Các nguồn hiện có gồm Facebook, Threads,
TikTok, VOZ và YouTube.

| Nền tảng | Đặc điểm ngữ liệu |
|---|---|
| Facebook | Bình luận trên group, page và bài đăng cụ thể |
| Threads | Bình luận ngắn, giàu tính hội thoại và phản ứng tức thời |
| TikTok | Bình luận và phản hồi liên quan đến video hoặc livestream |
| VOZ | Thảo luận dạng diễn đàn, thường có câu dài và nhiều ngữ cảnh |
| YouTube | Bình luận theo video, chủ đề đa dạng và có nhiều phản hồi ngắn |

Việc kết hợp nhiều nền tảng giúp bộ dữ liệu không phụ thuộc vào một phong cách
ngôn ngữ duy nhất. Tuy nhiên, mỗi nền tảng có đặc điểm người dùng và cơ chế
hiển thị khác nhau, do đó phân bố dữ liệu giữa các nền tảng cần được xem xét
khi phân tích kết quả.

## 3.4. Chuẩn hóa cấu trúc dữ liệu

Dữ liệu từ các crawler có định dạng khác nhau được ánh xạ về một schema chung.
Quá trình này chỉ thực hiện hợp nhất tên trường và cấu trúc, chưa biến đổi
nội dung bình luận.

Việc tách riêng bước merge và bước tiền xử lý giúp phân biệt rõ hai vấn đề:

- Sai khác do cấu trúc nguồn.
- Sai khác do nội dung văn bản.

Nhờ đó, các bản ghi có thể được thống kê theo nền tảng và kiểm tra các trường
bị thiếu trước khi thực hiện làm sạch văn bản.

## 3.5. Các tiêu chí tiền xử lý

### 3.5.1. Dữ liệu rỗng và dữ liệu lỗi

Các bản ghi không có nội dung bình luận, chỉ chứa khoảng trắng hoặc chỉ gồm
chuỗi ký hiệu không có giá trị ngữ nghĩa được xem là dữ liệu không hợp lệ.
Những bản ghi này được loại khỏi tập văn bản phân tích sau khi đã kiểm tra
riêng để tránh xóa nhầm bình luận ngắn nhưng có ý nghĩa, chẳng hạn như một từ
thể hiện cảm xúc hoặc một câu trả lời ngắn.

### 3.5.2. Thông tin nhận dạng cá nhân

Thông tin nhận dạng được xóa khỏi văn bản sử dụng cho nghiên cứu, thay vì
chuyển thành token giả. Nhóm thông tin cần loại bỏ gồm:

- Tên người dùng và tên người được tag.
- Địa chỉ email.
- Số điện thoại.
- URL cá nhân hoặc đường dẫn không cần thiết cho nội dung nghiên cứu.
- Các chuỗi có khả năng xác định trực tiếp một cá nhân.

Sau khi xóa, khoảng trắng được chuẩn hóa lại. Nếu bình luận không còn nội dung
có ý nghĩa thì được xem là rỗng sau tiền xử lý.

### 3.5.3. Spam, quảng cáo và nội dung không hữu ích

Các nội dung được xác định rõ là quảng cáo, spam hoặc chuỗi copy-paste hàng
loạt được loại khỏi dữ liệu phân tích. Một số dấu hiệu thường gặp gồm:

- Lặp lại cùng một nội dung trên nhiều bài đăng.
- Chứa nhiều đường dẫn hoặc thông tin liên hệ phục vụ quảng cáo.
- Nội dung bán hàng không liên quan đến chủ đề thảo luận.
- Chuỗi ký tự vô nghĩa hoặc nội dung hệ thống do crawler thu thập.
- Bình luận chỉ có thông tin quảng bá mà không có nội dung thảo luận.

Không nên xem một từ khóa đơn lẻ là bằng chứng đầy đủ của spam. Quyết định
loại cần dựa trên sự kết hợp giữa nội dung, tần suất lặp và ngữ cảnh nguồn.

### 3.5.4. Chuẩn hóa Unicode và khoảng trắng

Văn bản được chuẩn hóa Unicode về cùng một dạng, loại bỏ khoảng trắng thừa,
chuẩn hóa xuống dòng và loại bỏ khoảng trắng ở đầu hoặc cuối câu. Bước này
giúp những văn bản khác nhau về hình thức nhưng giống nhau về nội dung có thể
được so sánh nhất quán hơn.

### 3.5.5. Emoji và dấu câu

Emoji được xem là thành phần ngữ nghĩa quan trọng trong bình luận mạng xã hội,
đặc biệt trong các bài toán liên quan đến cảm xúc và thái độ. Vì vậy, emoji
được giữ nguyên, không rút gọn và không chuyển thành mô tả văn bản.

Các emoji cần được bảo toàn gồm:

```text
✅ ❤ 😂 😭 🥰 🤣 👍
```

Các biến thể Unicode của emoji, chẳng hạn `❤` và `❤️`, cũng không được tự ý
loại bỏ. Dấu câu cũng được giữ khi chúng góp phần thể hiện sắc thái như nhấn
mạnh, nghi vấn, mỉa mai hoặc cảm xúc.

### 3.5.6. Ngôn ngữ hỗn hợp

Ngữ liệu được chia thành các nhóm mô tả ngôn ngữ gồm tiếng Việt chủ yếu, tiếng
Anh chủ yếu, ngôn ngữ hỗn hợp, chỉ emoji/ký hiệu và không xác định. Không nên
loại ngay các bình luận ngắn, bình luận trộn tiếng Anh hoặc bình luận chỉ có
emoji, vì đây vẫn có thể là các quan sát hợp lệ của môi trường mạng xã hội.

## 3.6. Khử trùng lặp

Raw hiện chỉ giữ `row_id`, `platform`, `title` và `comment`, trong khi các mã
định danh nguồn như `comment_id`, `post_id` hoặc `video_id` không nằm trong
snapshot bốn trường. Vì vậy, không thể khẳng định mọi bình luận giống nội dung
là cùng một bản ghi bị thu thập lặp lại.

Quy trình khử trùng được chia thành hai giai đoạn.



### 3.6.1. Phát hiện bình luận trùng trong raw

Sau khi merge, tạo khóa so sánh từ nền tảng, tiêu đề và nội dung bình luận sau
khi chuẩn hóa Unicode, chữ hoa/thường và khoảng trắng. Emoji và dấu câu được
giữ trong khóa chính.

Các nhóm có cùng khóa chỉ được xem là ứng viên. Nếu hai bình luận xuất hiện ở
những bài đăng hoặc nền tảng khác nhau, chúng có thể là hai quan sát độc lập và
không nên bị xóa chỉ vì nội dung giống nhau.

Đối với near-duplicate, cần xem xét thêm từ phủ định, emoji và sắc thái câu.
Hai bình luận chỉ khác emoji có thể mang ý nghĩa cảm xúc trái ngược, do đó
không được xem là cùng một mẫu một cách máy móc.

### 3.6.2. Đánh giá và xử lý ứng viên trùng

Các ứng viên được kiểm tra dựa trên nền tảng, tiêu đề, nội dung, ngữ cảnh bài
đăng và thông tin định danh còn có trong dữ liệu. Chỉ những bản ghi có đủ cơ sở
cho thấy cùng một bình luận bị thu thập lặp lại mới được loại bỏ. Những bình
luận có nội dung giống nhau nhưng thuộc các bài đăng hoặc nền tảng khác nhau
được giữ lại vì có thể phản ánh các quan sát độc lập.

Nguyên tắc này giúp hạn chế việc làm giảm tính đa dạng của bộ dữ liệu và tránh
xóa nhầm các bình luận hợp lệ. Việc khử trùng lặp vì vậy được thực hiện thận
trọng, ưu tiên độ tin cậy của dữ liệu hơn việc giảm số lượng bản ghi.

## 3.7. Kết luận chương

Chương này đã trình bày phạm vi, nguồn dữ liệu, cấu trúc thống nhất và các
nguyên tắc tiền xử lý bộ dữ liệu bình luận mạng xã hội. Quy trình tập trung vào
việc loại bỏ dữ liệu rỗng, lỗi, thông tin nhận dạng cá nhân và nội dung không
hữu ích; đồng thời bảo toàn các yếu tố có thể mang ý nghĩa ngữ nghĩa như emoji,
dấu câu, teencode và ngôn ngữ hỗn hợp.

Bên cạnh đó, phương pháp khử trùng lặp được xây dựng theo hướng thận trọng,
không xem mọi bình luận giống nhau là bản ghi lặp. Cách tiếp cận này tạo cơ sở
cho việc hình thành một bộ dữ liệu có cấu trúc nhất quán, hạn chế mất mát thông
tin và phù hợp cho các bước phân tích tiếp theo.


