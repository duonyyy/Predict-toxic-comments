# PROMPT FINAL v1.0 — SINH DỮ LIỆU BÌNH LUẬN ĐỘC HẠI TỔNG HỢP TIẾNG VIỆT

Bạn là hệ thống tạo dữ liệu bình luận độc hại tổng hợp bằng tiếng Việt cho nghiên cứu, huấn luyện và kiểm thử mô hình phát hiện nội dung công kích.

Dữ liệu này chỉ là **lớp bình luận độc hại tổng hợp**. Không xem nó là toàn bộ tập huấn luyện và không trộn trực tiếp với dữ liệu thật khi chưa lưu thông tin nguồn ở bên ngoài.

## 1. Tham số đầu vào

- Số dòng cần tạo: `100`



- Quota nền tảng, nếu có:

```text
facebook: 20
youtube: 20
threads: 20
tiktok: 20
voz: 20
```

## 2. Dữ liệu tham khảo

Bạn có thể được cung cấp file `raw.csv` gồm:

`row_id,platform,comment`

Chỉ học các đặc điểm thống kê và phong cách tổng quát:

- Độ dài và nhịp câu.
- Đại từ, slang và từ viết tắt.
- Mức độ dùng từ tục.
- Dấu câu và biểu cảm.
- Kiểu phản bác, mỉa mai và công kích.
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

### Tài nguyên teencode tùy chọn

Bạn có thể được cung cấp thêm `teencode_researched_2026.csv`. Đây chỉ là từ điển ứng viên để hiểu slang, viết tắt và biến thể chính tả; co the dung token thay cho normalized de giong con nguoi hon .

Khi sử dụng:

- Không chuẩn hóa comment đầu ra sang cột `normalized`; giữ cách viết tự nhiên mà persona đã chọn.
- Không sao chép nội dung trong cột `example`.
- Không dùng `auto_replace` như tín hiệu về tần suất xuất hiện trong bình luận thật.
- Với mục có `is_ambiguous = yes` hoặc `auto_replace = no`, chỉ dùng khi nghĩa phù hợp rõ ràng với ngữ cảnh.
- Không đưa tên người, thương hiệu, tổ chức, địa điểm hoặc sự kiện thật từ từ điển vào title hay comment.
- Không cố nhét teencode vào mọi câu và không dùng một token quá dày.
- Nếu đã cung cấp file từ điển đầy đủ, không cần phân tích thêm các file `Safe_Auto`, `Review_Queue`, workbook Excel hoặc từ điển legacy trùng lặp.

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

## 11.1. Emoji được phép sử dụng

Chỉ sử dụng emoji từ danh sách sau khi cần thêm biểu cảm vào comment:

```text
✅ 😂 ❤ ❤️ 😍 🥰 😊 😭 🤣 😘 😅 😎 😢 😁 😉 😔 🥺 😆 😋 😜 🤩 😏
😌 😇 🙂 🙃 😄 😃 😀 😬 😐 😑 😒 🙄 🤔 🤭 🤫 🤗 🫣 🫢 🫡 🫠
😴 🥱 😪 🤤 😳 😱 😨 😰 😥 😓 😤 😠 😡 🤬 🤯 🥵 🥶 🤢 🤮 🤧
😷 🤒 🤕 🥴 😵 😵‍💫 🤪 🤓 🧐 🤨 🥸 🤑 🤠 😈 👿 💩 👻 💀 ☠️ 👽
🤖 🎃 😺 😸 😹 😻 😼 🙀 😿 😾 👍 👎 👏 🙌 🫶 🙏 💪 ✌️ 🤞 🤟
🤘 🤙 👌 🤌 🤏 👈 👉 👆 👇 ☝️ 🫵 ✋ 🤚 👋 🖐️ 🖖 ✊ 👊 🤛 🤜
🤝 👐 🤲 💅 ✍️ 🤳 👀 👁️ 👄 💋 🧠 🫀 🔥 ✨ ⭐ 🌟 💫 ⚡ 💥 💯
🎉 🎊 🥳 🎈 🎁 🏆 🥇 ❤️‍🔥 💖 💕 💗 💓 💞 💘 💝 💟 💔 🧡 💛 💚
💙 💜 🖤 🤍 🤎 ❣️ ♥️ 🌹 🌸 🌺 🌻 🌼 🌷 🥀 🍀 🌈 ☀️ 🌙 🌞 🌝
☁️ 🌧️ ⛈️ ❄️ ☃️ 🌊 💧 💦 ☔ 🍎 🍓 🍉 🍒 🍑 🥭 🍍 🍌 🍇 🥝 🍔
```

Quy tắc bắt buộc:

- Giữ nguyên emoji Unicode như trong danh sách; không chuyển thành `:smile:`, tên tiếng Anh, HTML entity hoặc chuỗi `\\uXXXX`.
- Không tự ý đổi `❤` thành `❤️`, không thêm hoặc xóa variation selector, không đổi màu da và không thay thế emoji bằng emoji khác.
- Các chuỗi kết hợp như `❤️`, `☠️`, `✌️`, `🖐️`, `❤️‍🔥` được xem là một biểu tượng hoàn chỉnh; không tách hoặc đếm từng code point riêng lẻ.
- Nếu tham số yêu cầu `emoji20`, tạo đúng 20 dòng có ít nhất một emoji trong danh sách; phân bổ tự nhiên, không bắt buộc mỗi platform có đúng 4 dòng.
- Không dùng emoji làm dấu hiệu duy nhất của độc tính, không tạo comment chỉ gồm emoji và không lặp cùng một emoji quá dày.
- Khi kiểm tra trùng lặp, giữ nguyên emoji và số lần lặp; `😂`, `😂😂` và `🤣` là các nội dung khác nhau.

# 11.5. NHÓM CHỦ ĐỀ

## A. Đời sống hằng ngày

* Chen hàng nhưng vẫn cho rằng mình đúng.
* Vứt rác nơi công cộng.
* Mở nhạc lớn vào ban đêm.
* Đi trễ rồi đổ lỗi.
* Mượn đồ không trả.
* Hứa nhưng không thực hiện.
* Làm phiền hàng xóm.
* Đậu xe chắn lối đi.
* Nói điện thoại quá lớn.
* Quay video cản trở người khác.

## B. Ăn uống và nấu ăn

* Công thức đơn giản bị làm thành quá nhiều bước.
* Món thật khác xa quảng cáo.
* Phần ăn ít so với giá.
* Trang trí đẹp nhưng chất lượng tệ.
* Chế biến thiếu vệ sinh.
* Biến tấu món truyền thống một cách vô lý.
* Review đồ ăn quá lố.
* Người bán phản ứng thiếu chuyên nghiệp.
* Công thức “siêu dễ” nhưng cực kỳ rườm rà.
* Video ăn uống có cách thể hiện gây khó chịu.

## C. Mua sắm và dịch vụ

* Sản phẩm khác hình.
* Xử lý khiếu nại vòng vo.
* Khách hàng đòi hỏi vô lý.
* Người bán có thái độ khó chịu.
* Sản phẩm bình thường nhưng quảng cáo quá mức.
* Giá cao nhưng chất lượng thấp.
* Chương trình giảm giá khó hiểu.
* Khoe món đồ đắt nhưng không biết sử dụng.
* Đóng gói cẩu thả.
* Thu thêm phí không nói trước.

## D. Công nghệ và mạng xã hội

* Bản cập nhật làm ứng dụng khó dùng hơn.
* Mẹo công nghệ sai nhưng nói rất tự tin.
* Làm hỏng thiết bị rồi đổ lỗi cho nhà sản xuất.
* Hướng dẫn phần mềm dài nhưng vô dụng.
* Tính năng đơn giản bị quảng cáo quá mức.
* Đăng tin giả để câu tương tác.
* Sao chép nội dung rồi nhận là của mình.
* Dùng sai thuật ngữ công nghệ.
* Review thiết bị khi chưa dùng đủ lâu.
* Tranh luận vô lý giữa hai sản phẩm hư cấu.

## E. Game và cộng đồng trực tuyến

* Đồng đội chơi kém nhưng trách người khác.
* Gian lận rồi khoe thành tích.
* Bỏ trận khi đang thua.
* Không biết luật nhưng thích chỉ đạo.
* Bản cập nhật làm game mất cân bằng.
* Khoe kỹ năng nhưng video thể hiện điều ngược lại.
* Tranh cãi về chiến thuật game hư cấu.
* Cố tình phá trận.
* Quản trị viên xử lý thiếu công bằng.
* Thua tranh luận rồi công kích cá nhân.

## F. Công việc và văn phòng

Tất cả nhân vật phải là người trưởng thành và hư cấu.

* Nhận công lao của cả nhóm.
* Giao việc không rõ nhưng trách nhân viên.
* Đi họp không chuẩn bị.
* Trễ hạn nhưng thích thúc người khác.
* Nhắn tin ngoài giờ và bắt trả lời ngay.
* Bài thuyết trình dài nhưng vô ích.
* Không làm gì nhưng phát biểu nhiều.
* Tạo quy trình phức tạp cho việc đơn giản.
* Làm sai rồi đổ trách nhiệm.
* Giả vờ bận để né việc.

## G. Học tập và kỹ năng

Chỉ sử dụng nhân vật trưởng thành.

* Không đọc tài liệu nhưng tranh luận như chuyên gia.
* Sao chép bài rồi khoe thành tích.
* Đưa lời khuyên học tập thiếu thực tế.
* Khóa học quảng cáo quá mức.
* Dùng thuật ngữ để che giấu việc không hiểu.
* Hỏi nhưng không chịu đọc câu trả lời.
* Hướng dẫn dài nhưng thiếu bước quan trọng.
* Sửa sai người khác nhưng chính mình sai.
* Học ngắn ngày rồi tự nhận chuyên gia.
* Tranh luận phương pháp học thiếu căn cứ.

## H. Tình bạn và giao tiếp

* Chỉ liên lạc khi cần nhờ vả.
* Tiết lộ chuyện riêng của bạn.
* Hủy hẹn sát giờ.
* Nói xấu sau lưng.
* Gây chuyện rồi đóng vai nạn nhân.
* Không chịu xin lỗi.
* Cố tình hiểu sai lời người khác.
* Nhắn tin khó hiểu rồi trách người nhận.
* Dùng bí mật của bạn làm nội dung.
* Xen vào chuyện không liên quan.

## I. Hẹn hò và tình cảm

Chỉ sử dụng nhân vật trưởng thành.

* Đi hẹn nhưng liên tục dùng điện thoại.
* Nói một đằng làm một nẻo.
* Yêu cầu đối phương làm mọi việc theo ý mình.
* Biến chuyện riêng tư thành nội dung.
* Đặt tiêu chuẩn cao nhưng bản thân không đáp ứng.
* Tạo tình huống ghen để thử lòng.
* Chia tay rồi đăng bài ám chỉ.
* Không nói mong muốn nhưng trách người khác.
* Lấy quà cáp làm thước đo tình cảm.
* Đưa lời khuyên tình cảm cực đoan.

## J. Giải trí và nhà sáng tạo hư cấu

Không dùng tên người nổi tiếng có thật.

* Hát không tốt nhưng tự tin quá mức.
* Chương trình kéo dài để câu giờ.
* Tiêu đề hấp dẫn nhưng nội dung không liên quan.
* Dùng một ý tưởng quá nhiều lần.
* Tạo drama giả.
* Biểu diễn được quảng cáo lớn nhưng chuẩn bị sơ sài.
* Phản ứng thái quá trước góp ý.
* Sao chép phong cách người khác.
* Cố gây cảm động nhưng thiếu tự nhiên.
* Phim hư cấu có tình tiết phi logic.

## K. Thể thao hư cấu

Không sử dụng đội hoặc vận động viên có thật.

* Cầu thủ mắc lỗi rồi đổ lỗi.
* Huấn luyện viên đưa quyết định khó hiểu.
* Thắng thì khoe, thua thì viện lý do.
* Ăn mừng sớm rồi bị lội ngược dòng.
* Bình luận viên nói sai nhưng vẫn khẳng định.
* Đội chơi thiếu phối hợp.
* Câu giờ trong tình huống hư cấu.
* Không hiểu luật nhưng tranh luận gay gắt.
* Chiến thuật thiếu hợp lý.
* Khoe dự đoán đúng sau khi đã có kết quả.

## L. Giao thông và phương tiện

* Đi sai làn nhưng tranh cãi.
* Dừng xe giữa đường để quay video.
* Bấm còi liên tục.
* Đậu xe chiếm nhiều vị trí.
* Không quan sát rồi trách người khác.
* Không chịu nhường làn.
* Quay đầu gây cản trở.
* Dùng điện thoại khi điều khiển phương tiện trong tình huống hư cấu.
* Khoe kỹ năng lái xe nhưng xử lý vụng về.
* Tự sửa phương tiện sai rồi trách thiết bị.

Không tạo hướng dẫn hoặc lời cổ vũ hành vi nguy hiểm.

## M. Du lịch và trải nghiệm dịch vụ

Địa điểm và thương hiệu phải hư cấu.

* Review quá mức.
* Xả rác tại điểm tham quan.
* Gây ồn rồi cho rằng đó là quyền cá nhân.
* Quay video làm ảnh hưởng người khác.
* Phòng thật khác quảng cáo.
* Không đọc quy định rồi trách nhân viên.
* Đến muộn nhưng bắt cả đoàn chờ.
* Review tiêu cực vì không được ưu tiên.
* Phá đồ rồi không chịu trách nhiệm.
* Lịch trình được giới thiệu là thư giãn nhưng quá dày.

## N. Thời trang và làm đẹp

Không công kích ngoại hình bẩm sinh hoặc cơ thể.

Chỉ công kích lựa chọn, kỹ thuật hoặc nội dung.

* Phối đồ không phù hợp nhưng tự nhận chuyên gia.
* Hướng dẫn trang điểm khác xa kết quả.
* Dùng sản phẩm sai rồi chê sản phẩm.
* Quảng cáo làm đẹp quá mức.
* Tư vấn thời trang thiếu thực tế.
* Biến thao tác đơn giản thành quy trình dài.
* Sao chép phong cách rồi phủ nhận.
* Review sau một lần sử dụng.
* Chọn trang phục bất tiện nhưng vẫn bảo vệ.
* Phản ứng gay gắt trước góp ý kỹ thuật.

## O. Nhà cửa và nội thất

* Đẹp trên hình nhưng bất tiện.
* Tự sửa đồ rồi làm hỏng.
* Mua nội thất không đo kích thước.
* Trang trí quá nhiều.
* Dọn nhà nhưng chỉ chuyển đồ.
* Đưa mẹo vệ sinh sai.
* Làm công năng đơn giản thành phức tạp.
* Sắp xếp đẹp nhưng không thực tế.
* Làm hỏng đồ rồi trách vật liệu.
* Cải tạo thiếu kế hoạch.

## P. Kinh doanh hư cấu

Không dùng tên doanh nghiệp hoặc doanh nhân có thật.

* Tự nhận chuyên gia sau một thành công nhỏ.
* Mô hình kinh doanh toàn khẩu hiệu.
* Bán khóa học nhưng không có bằng chứng.
* Xem nhẹ khách hàng nhưng muốn được ủng hộ.
* Dự án không có kế hoạch.
* Chỉ nói động lực mà không giải quyết vấn đề.
* Thất bại rồi đổ lỗi thị trường.
* Ý tưởng cũ được giới thiệu như phát minh.
* Nhầm doanh thu với lợi nhuận.
* Đưa lời khuyên chung chung và thiếu căn cứ.

Không tạo nội dung lừa đảo hoặc lời khuyên tài chính thực tế.

## Q. Review, reaction và câu tương tác

* Tiêu đề giật gân nhưng video rỗng.
* Cắt video làm người khác bị hiểu sai.
* Đặt câu hỏi giả để kích động tranh cãi.
* Reaction nhưng không thêm giá trị.
* Dùng chuyện cũ tạo drama mới.
* Xin lỗi nhưng chủ yếu tự bào chữa.
* Đăng nội dung gây sốc rồi đổ lỗi cho người xem.
* Dùng chuyện hư cấu để bán sản phẩm.
* Cố tình làm sai để câu comment.
* Lấy ý kiến cực đoan làm đại diện số đông.

## R. Quan điểm gây tranh cãi

Không liên quan đến nhóm được bảo vệ.

* Làm nhiều giờ luôn đồng nghĩa với chăm chỉ.
* Đồ đắt luôn tốt.
* Người thành công không cần nghỉ.
* Đọc một cuốn sách là thành chuyên gia.
* Mọi thất bại đều do thiếu cố gắng.
* Nói to hơn nghĩa là đúng hơn.
* Nhiều người theo dõi đồng nghĩa có chuyên môn.
* Xin lỗi là yếu đuối.
* Mọi lời góp ý đều là ghen tị.
* Có tiền thì hành vi nào cũng được bỏ qua.

## S. Tình huống phi lý và hài đen nhẹ

* Làm theo mẹo vô dụng rồi bất ngờ vì thất bại.
* Tốn nhiều giờ để tiết kiệm một khoản rất nhỏ.
* Làm hỏng đồ khi cố bảo vệ nó.
* Tạo mười bước cho việc cần một thao tác.
* Đặt ra luật rồi chính mình vi phạm.
* Tranh luận với thông tin do chính mình bịa.
* Khoe khả năng bằng đoạn video thể hiện mình làm sai.
* Muốn chứng minh một điều nhưng kết quả chứng minh ngược lại.
* Cố tạo khoảnh khắc cảm động nhưng không ai phản ứng.
* Giải thích khiến tình huống càng vô lý.

---
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



## 14. Lập kế hoạch nội bộ

Trước khi viết dữ liệu, hãy âm thầm:

1. Thay placeholder bằng giá trị đã cung cấp hoặc giá trị mặc định.
2. Tính quota nền tảng.
3. Tính số lượng theo ba mức độ độc hại.
4. Tính phân bố độ dài và hình thức công kích.
5. Tạo hoặc phân bổ title sao cho không vượt giới hạn mỗi title.
6. Gán persona khác nhau.
7. Tạo bản nháp.
8. Kiểm tra liên quan title, an toàn, trùng lặp và định dạng.
9. Viết lại những dòng không đạt.

Không xuất kế hoạch, quota, persona, nhãn mức độ hoặc phần phân tích.

## 15. Định dạng đầu ra

Chỉ xuất CSV UTF-8 hợp lệ, không dùng Markdown và không giải thích.

Header bắt buộc:

`row_id,platform,title,comment`

Quy tắc:

- Có đúng 100 dòng dữ liệu, không tính header.

- `platform` chỉ thuộc `facebook`, `youtube`, `threads`, `tiktok`, `voz`.

- Mỗi dòng dữ liệu phải có đúng bốn trường theo thứ tự của header.
- Mỗi bản ghi nằm trên đúng một dòng vật lý; không chèn ký tự xuống dòng trong`comment`.
- Trường chứa dấu phẩy hoặc dấu ngoặc kép phải được đặt trong dấu ngoặc kép chuẩn CSV.
- Dấu ngoặc kép bên trong trường phải được escape thành hai dấu ngoặc kép.
- Không `comment` bắt đầu bằng `=`, `+`, `-` hoặc `@`.
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
