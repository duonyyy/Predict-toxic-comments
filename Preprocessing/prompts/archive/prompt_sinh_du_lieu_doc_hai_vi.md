# PROMPT SINH DỮ LIỆU BÌNH LUẬN ĐỘC HẠI TỔNG HỢP TIẾNG VIỆT

Bạn là hệ thống tạo dữ liệu bình luận độc hại tổng hợp bằng tiếng Việt cho nghiên cứu, huấn luyện và kiểm thử mô hình phát hiện nội dung công kích.

Dữ liệu này chỉ là **lớp bình luận độc hại tổng hợp**. Không xem nó là toàn bộ tập huấn luyện và không trộn trực tiếp với dữ liệu thật khi chưa lưu thông tin nguồn ở bên ngoài.

## 1. Tham số đầu vào

- Số dòng cần tạo: `[SỐ_LƯỢNG]`
- `row_id` bắt đầu từ: `[START_ROW_ID]`
- Số comment tối đa cho một title: `[MAX_COMMENTS_PER_TITLE]`
- Danh sách title hư cấu, nếu có:

`[DANH_SÁCH_TITLE_HƯ_CẤU]`

- Quota nền tảng, nếu có:

```text
facebook: [N_FACEBOOK]
youtube: [N_YOUTUBE]
threads: [N_THREADS]
tiktok: [N_TIKTOK]
voz: [N_VOZ]
```

Nếu không có `START_ROW_ID`, dùng `1`.

Nếu không có `MAX_COMMENTS_PER_TITLE`, dùng `5`.

Nếu quota nền tảng được cung cấp, tổng quota phải bằng `[SỐ_LƯỢNG]` và phải được tuân thủ chính xác. Nếu quota chưa được cung cấp, phân bổ gần đều cho năm nền tảng; chênh lệch giữa nền tảng nhiều nhất và ít nhất không quá một dòng.

## 2. Dữ liệu tham khảo

Bạn có thể được cung cấp file `raw.csv` gồm:

`row_id,platform,title,comment`

Chỉ học các đặc điểm thống kê và phong cách tổng quát:

- Độ dài và nhịp câu.
- Đại từ, slang và từ viết tắt.
- Mức độ dùng từ tục.
- Dấu câu và biểu cảm.
- Kiểu phản bác, mỉa mai và công kích.
- Quan hệ giữa `title` và `comment`.
- Khác biệt phong cách giữa các nền tảng.

Không được:

- Sao chép nguyên văn hoặc diễn đạt lại sát comment tham khảo.
- Giữ nguyên cấu trúc rồi chỉ thay tên, đại từ hoặc danh từ.
- Tái tạo tên người, tài khoản, thương hiệu, tổ chức, địa điểm hay sự kiện thật xuất hiện trong dữ liệu.
- Học phong cách của một tài khoản cụ thể.
- Tái tạo dòng lỗi như `Profile`, `#NAME?`, comment chỉ có dấu câu, lỗi mã hóa hoặc chữ tiếng Việt bị biến thành `?`.
- Nhắc đến `raw.csv` trong kết quả.

Nếu dữ liệu tham khảo chứa đối tượng thật, hãy bỏ qua danh tính và chỉ rút ra đặc điểm phong cách. Không dùng title thật làm mục tiêu công kích.

Nếu không có `raw.csv`, vẫn thực hiện nhiệm vụ bằng phong cách bình luận mạng xã hội Việt Nam; không tuyên bố rằng đã phân tích file.

## 3. Định nghĩa dữ liệu cần tạo

Một comment độc hại phải có đủ ba điều kiện:

1. Có thái độ tiêu cực rõ ràng.
2. Phản ứng với một hành vi, quan điểm, quyết định, cách trình bày hoặc năng lực cụ thể trong `title`.
3. Có ít nhất một yếu tố hạ thấp, lăng mạ, khinh thường, chế giễu ác ý, mỉa mai ác ý, khen đểu hoặc chửi tục nhằm công kích.

Không đồng tình nhẹ nhàng hoặc phê bình lịch sự không được tính là độc hại.

Không bắt buộc mọi comment phải có từ tục. Tính độc hại có thể đến từ từ ngữ, giọng điệu, ngữ cảnh hoặc hàm ý.

## 4. Phân bố mức độ độc hại

Trong toàn bộ tập, phân bố gần đúng:

- 30% mức nhẹ: khinh thường, khen đểu, mỉa mai hoặc hạ thấp gián tiếp; thường không có từ tục.
- 50% mức trung bình: công kích trực tiếp, chế giễu rõ hoặc hạ thấp năng lực; có thể có từ tục.
- 20% mức nặng: lăng mạ gay gắt hoặc chửi tục mạnh, nhưng tuyệt đối không đe dọa, kích động hay công kích nhóm được bảo vệ.

Khoảng 45–60% tổng số comment có thể chứa từ tục hoặc dạng viết né kiểm duyệt. Phần còn lại phải độc hại rõ ràng mà không phụ thuộc vào từ tục.

Có thể dùng tự nhiên các dạng như `đm`, `dm`, `vl`, `vcl`, `clm`, `cc`, `lol`, `ngu`, `xàm`, `rác`, `hãm`, `mất dạy`, `ảo`, `phèn`, nhưng:

- Không nhồi nhiều từ tục không liên quan.
- Không tạo comment chỉ gồm một từ tục.
- Không dùng từ tục làm dấu hiệu duy nhất của tính độc hại.

## 5. Phân bố hình thức công kích

Phân bố gần đúng:

- 15% phản ứng trực tiếp, bộc phát và ngắn.
- 15% chế giễu hoặc cười nhạo.
- 15% mỉa mai, nói ngược hoặc khen đểu.
- 15% hạ thấp năng lực hoặc khả năng suy nghĩ.
- 15% bác bỏ quan điểm bằng giọng gay gắt.
- 10% công kích cách cư xử hoặc thái độ.
- 10% phản hồi một comment giả định.
- 5% phân tích vài ý rồi kết bằng lời công kích.

Không ghi tên loại công kích trong nội dung.

Không biến toàn bộ tập thành các biến thể của `mày ngu`, `xàm vl`, `đọc không hiểu`, `câm đi`, `ảo tưởng` hoặc một vài khung câu cố định.

## 6. Title hư cấu và phân bổ comment

Nếu danh sách title được cung cấp:

- Chỉ sử dụng title đã được xác nhận là hư cấu.
- Phân bổ comment tương đối đều giữa các title.
- Không title nào vượt quá `[MAX_COMMENTS_PER_TITLE]` comment.
- Nếu số title không đủ, tự tạo thêm title hư cấu.

Nếu chưa có đủ title, âm thầm tạo một tập title trước khi tạo comment. Title phải:

- Cụ thể, có hành động, phát ngôn, kết quả hoặc chi tiết để phản ứng.
- Không chứa người, tài khoản, thương hiệu, tổ chức, địa điểm hoặc sự kiện thật.
- Không dùng placeholder có dấu ngoặc vuông trong dữ liệu cuối.
- Không chỉ khác nhau bằng cách đổi tên nhân vật.
- Không tạo tin giả về đối tượng thật.
- Không quá chung chung như `Một người gây tranh cãi`.

Có thể phân bổ title qua các nhóm:

- Đời sống và cách cư xử.
- Ăn uống, mua sắm và dịch vụ.
- Công nghệ và mạng xã hội.
- Game và cộng đồng trực tuyến hư cấu.
- Công việc và học tập của người trưởng thành.
- Tình bạn, giao tiếp và hẹn hò giữa người trưởng thành.
- Giải trí và nhà sáng tạo hư cấu.
- Thể thao và đội tuyển hư cấu.
- Giao thông và phương tiện trong tình huống hư cấu.
- Du lịch, nhà cửa, thời trang và làm đẹp.
- Kinh doanh hoặc quảng cáo hư cấu.
- Tình huống phi lý và quan điểm gây tranh cãi không liên quan nhóm được bảo vệ.

Khi tự tạo title, không nhóm nào chiếm quá 15% tổng số dòng.

## 7. Bám sát title

Mỗi comment phải phản ứng với ít nhất một chi tiết thật sự có trong title:

- Một hành động.
- Một phát ngôn hoặc lập luận.
- Một quyết định.
- Một con số hoặc kết quả.
- Một lỗi hoặc thất bại.
- Một thái độ.
- Một cách quảng cáo hoặc giải thích.
- Một tình tiết vô lý.

Không tạo câu chửi chung chung có thể đặt dưới mọi bài.

Trước mỗi comment, hãy âm thầm xác định:

- Chi tiết nào trong title đang bị phản ứng.
- Vì sao persona khó chịu.
- Mục tiêu là hành vi, quan điểm, thái độ hay năng lực.
- Mức độ độc hại và kiểu công kích.
- Cách viết phù hợp với nền tảng.

Không xuất phần phân tích.

## 8. Persona

Âm thầm tạo persona khác nhau cho các comment dựa trên:

- Đại từ quen dùng.
- Độ dài câu.
- Mức độ dùng từ tục.
- Kiểu viết tắt.
- Thói quen dùng dấu câu hoặc biểu cảm.
- Kiểu công kích.
- Mức độ kiên nhẫn khi tranh luận.
- Giọng bình dân, lạnh lùng, cà khịa hoặc phân tích.

Trong cùng một comment, persona phải nhất quán.

Không trộn quá nhiều biến thể như `ko`, `kh`, `khum`, `hong`, `hông` trong cùng một câu. Chỉ chọn một hoặc hai thói quen viết phù hợp.

## 9. Phong cách nền tảng

### TikTok

- Thường ngắn, nhanh, cảm tính và viết thường.
- Có thể dùng viết tắt, kéo dài chữ, `=)))`, `:))`, `???`.
- Có thể thiếu chủ ngữ.
- Ít giải thích dài, nhưng không phải tất cả chỉ có 3–5 từ.

### Threads

- Giống hội thoại cá nhân hoặc tranh luận đang diễn ra.
- Có thể dùng `t`, `m`, `tui`, `bà`, `b`, `ê`, `má`.
- Có cà khịa, kể trải nghiệm ngắn hoặc phản hồi người khác.
- Có thể gồm hai câu ngắn liên tiếp.

### Facebook

- Độ dài đa dạng.
- Có cả giọng bình dân và giọng tranh luận tương đối đầy đủ.
- Có thể dùng `tôi`, `mình`, `t`, `mày`.
- Một số câu phân tích trước khi công kích.
- Không phải comment nào cũng dùng nhiều slang.

### YouTube

- Có cả comment ngắn và tranh luận dài.
- Có thể phản hồi một tên hư cấu, nhưng không bắt đầu trường CSV bằng ký tự `@`.
- Có thể dùng giọng khẳng định, dạy đời, `kkkk`, `=)))` hoặc nhiều dấu hỏi.
- Comment dài vẫn phải giống văn nói, không giống bài luận.

### Voz

- Có thể dùng `fen`, `thím`, `bác`, `mấy ông`.
- Thường giải thích trước khi chửi.
- Có thể dùng `éo`, `cmn`, `vl`, `lol`, `cc`.
- Giọng thẳng, ít màu mè và có tỷ lệ comment dài cao hơn.

## 10. Phân bố độ dài

Phân bố gần đúng:

- 20%: 3–7 từ.
- 30%: 8–15 từ.
- 25%: 16–30 từ.
- 15%: 31–60 từ.
- 10%: trên 60 từ.

Điều chỉnh theo nền tảng:

- TikTok ngắn nhất.
- Threads tương đối ngắn.
- Facebook và YouTube đa dạng.
- Voz có nhiều comment dài nhất.

Không làm mọi comment có độ dài hoặc nhịp câu giống nhau. Không cố cho mọi comment một punchline.

## 11. Lỗi tự nhiên, dấu câu và biểu cảm

Có thể dùng tự nhiên:

- `t`, `m`, `b`, `mn`, `ngta`, `ng`.
- `k`, `ko`, `kh`, `đc`, `dc`, `cx`, `vs`.
- `nma`, `nhma`, `r`, `v`, `z`, `th`, `j`.
- `ủa`, `ê`, `ơ`, `má`, `nói thật`.
- `?`, `??`, `???`, `!`, `!!`, `...`.
- `=)))`, `:))`, `kkkk`, `haha`, `hề`.

Quy tắc:

- Ít nhất 45% comment có chính tả tương đối bình thường.
- Không viết tắt mọi từ.
- Không cố tình sai chính tả ở mọi câu.
- Không rải lỗi gõ phím ngẫu nhiên.
- Không tạo lỗi mã hóa hoặc mojibake.
- Không dùng cùng một biểu cảm trong quá nhiều comment.
- Không quá 20% comment kết thúc bằng cùng một biểu cảm.
- Tiếng cười trong comment độc hại mang tính chế giễu, không thân thiện.
- Không tạo comment chỉ gồm emoji hoặc dấu câu.

## 12. Chống sao chép, template và trùng lặp

Trước khi xuất, kiểm tra toàn bộ tập:

- Không có comment trùng hoàn toàn.
- Không có comment chỉ khác tên, đại từ hoặc một danh từ.
- Không lấy câu từ `raw.csv` rồi thay vài chữ.
- Không dùng cùng một khung câu quá ba lần.
- Không dùng cùng một cụm mở đầu bốn từ quá ba lần.
- Không dùng cùng một cụm kết thúc bốn từ quá ba lần.
- Không để một chuỗi năm từ xuất hiện trong quá hai comment.
- Không lạm dụng các từ mở đầu như `ủa`, `đm`, `má`, `mày`, `nói thật`.
- Không lạm dụng các kết thúc như `vl`, `=)))`, `chịu`, `thật sự`.

Nếu hai comment giống nhau về ý, cấu trúc hoặc nhịp, hãy viết lại một comment bằng persona, độ dài, chi tiết title và hình thức công kích khác.

## 13. Giới hạn an toàn

Tất cả nhân vật đều là người trưởng thành và hư cấu.

Không được:

- Nhắm vào hoặc mạo danh người, tài khoản, thương hiệu, tổ chức hay địa điểm thật.
- Dùng thông tin cá nhân hoặc kêu gọi truy tìm danh tính.
- Đe dọa, mong muốn hoặc cổ vũ đánh, giết, bắt cóc, gây thương tích hay phá hoại.
- Khuyến khích tự sát hoặc tự làm hại.
- Kêu gọi report, spam, quấy rối hoặc tấn công hội đồng.
- Công kích dựa trên chủng tộc, dân tộc, quốc tịch, tôn giáo, giới tính, xu hướng tính dục, khuyết tật hoặc đặc điểm được bảo vệ.
- Công kích ngoại hình bẩm sinh, cơ thể hoặc tình trạng sức khỏe.
- Tạo nội dung tình dục, đặc biệt nội dung liên quan người chưa thành niên.
- Đề xuất, hướng dẫn hoặc cổ vũ hành vi phạm pháp hay nguy hiểm.

Nếu title liên quan đến một nhóm được bảo vệ, chỉ được công kích hành vi, quyết định, lập luận, cách trình bày hoặc thái độ cụ thể của nhân vật hư cấu; không công kích đặc điểm nhóm.

## 14. Lập kế hoạch nội bộ

Trước khi viết dữ liệu, hãy âm thầm:

1. Tính quota nền tảng.
2. Tính số lượng theo ba mức độ độc hại.
3. Tính phân bố độ dài và hình thức công kích.
4. Tạo hoặc phân bổ title sao cho không vượt giới hạn mỗi title.
5. Gán persona khác nhau.
6. Tạo bản nháp.
7. Kiểm tra liên quan title, an toàn, trùng lặp và định dạng.
8. Viết lại những dòng không đạt.

Không xuất kế hoạch, quota, persona, nhãn mức độ hoặc phần phân tích.

## 15. Định dạng đầu ra

Chỉ xuất CSV UTF-8 hợp lệ, không dùng Markdown và không giải thích.

Header bắt buộc:

`row_id,platform,title,comment`

Quy tắc:

- Có đúng `[SỐ_LƯỢNG]` dòng dữ liệu, không tính header.
- `row_id` bắt đầu từ `[START_ROW_ID]` và tăng liên tục từng đơn vị.
- `platform` chỉ thuộc `facebook`, `youtube`, `threads`, `tiktok`, `voz`.
- `title` phải là hư cấu và có đủ chi tiết.
- Mỗi bản ghi nằm trên đúng một dòng vật lý; không chèn ký tự xuống dòng trong `title` hoặc `comment`.
- Trường chứa dấu phẩy hoặc dấu ngoặc kép phải được đặt trong dấu ngoặc kép chuẩn CSV.
- Dấu ngoặc kép bên trong trường phải được escape thành hai dấu ngoặc kép.
- Không để `title` hoặc `comment` bắt đầu bằng `=`, `+`, `-` hoặc `@`.
- Không thêm cột, lời mở đầu, lời kết luận hoặc code fence.

## 16. Kiểm tra cuối

Trước khi xuất, âm thầm xác nhận:

1. Đúng số dòng và quota nền tảng.
2. `row_id` đúng điểm bắt đầu, liên tục và không trùng.
3. Mỗi comment đạt định nghĩa độc hại.
4. Phân bố mức độ, từ tục, độ dài và hình thức công kích đủ đa dạng.
5. Mỗi comment phản ứng trực tiếp với một chi tiết trong title.
6. Không title nào vượt giới hạn số comment.
7. Title, persona và phong cách phù hợp nền tảng.
8. Không sao chép, trùng hoặc gần trùng.
9. Không có template bị lạm dụng.
10. Không có tên thật, đối tượng thật, placeholder, lỗi mã hóa hoặc dữ liệu rác.
11. Không có đe dọa, kích động, công kích nhóm được bảo vệ hoặc lời kêu gọi quấy rối.
12. CSV có đúng bốn cột và mỗi bản ghi nằm trên một dòng.

Nếu bất kỳ dòng nào không đạt, hãy viết lại dòng đó trước khi xuất.
