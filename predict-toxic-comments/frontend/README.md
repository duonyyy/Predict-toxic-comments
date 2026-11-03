# Frontend - StreamGuard AI (Toxic Comment Monitor)

Giao diện giám sát & điều hành bình luận độc hại YouTube Live thời gian thực bằng AI. Dự án xây dựng trên **Next.js 16** (App Router), **React 19**, **Tailwind CSS 4**, **Framer Motion**, và **Recharts**.

---

## 🌟 Các cải tiến giao diện chính (UI/UX)

- **Giao diện Giám sát Hiện đại (Cyber Dark Theme):** Phong cách Glassmorphism với nền tối cao cấp, hiệu ứng ánh sáng động và chỉ báo nhịp thở realtime.
- **Thanh Chỉ số Tổng quan (KPI Stat Cards):**
  - **Tổng bình luận đã quét** (kèm trạng thái luồng trực tiếp).
  - **Tỉ lệ độc hại & Mức độ an toàn** (An toàn / Trung bình / Cảnh báo / Nguy hiểm).
  - **Số đối tượng vi phạm** đã bị gắn cờ.
  - **Thống kê phân loại hành động tự động:** Đếm số lượng Ban, Hide, Safe.
- **Bộ lọc & Tìm kiếm Bình luận Trực tiếp (Message List):**
  - Tìm kiếm bình luận theo tên tác giả hoặc nội dung.
  - Bộ lọc nhanh theo tab: *Tất cả*, *Chỉ Độc Hại*, *Cần Xử Lý (Ban/Hide)*, *An Toàn*.
  - Huy hiệu phân loại 5 nhãn độc hại chi tiết (`toxic`, `severe_toxic`, `threat`, `insult`, `identity_hate`).
  - Nút sao chép nội dung bình luận nhanh và nút chuyển đổi **Tự động cuộn / Tạm dừng** để kiểm duyệt viên đọc kỹ.
- **Biểu đồ Độc hại Đa chế độ (Toxicity Trend Chart):**
  - Chuyển đổi linh hoạt giữa: *Tất cả chỉ số*, *Số lượng Toxic*, *Tỉ lệ % Độc hại*.
  - Thống kê tự động tỉ lệ độc hại cao điểm (Peak) và hiện tại (Current).
- **Bảng Xếp hạng Vi Phạm (Toxic Leaderboard):**
  - Huy chương Top 1 🥇, Top 2 🥈, Top 3 🥉.
  - Thanh đo mức độ vi phạm trực quan cho từng người dùng.
- **Trải nghiệm Nhập liệu URL (Hero Controls):**
  - Nút xóa nhanh URL.
  - Nút **"Dùng thử URL stream mẫu"** hỗ trợ test nhanh khi chưa có sẵn link live.

---

## 🚀 Hướng dẫn Cài đặt & Chạy

### 1. Cài đặt thư viện:
```bash
cd frontend
npm install
```

### 2. Cấu hình file `.env.local` (nếu cần):
```env
NEXT_PUBLIC_API_URL=http://localhost:5000
```

### 3. Chạy ở môi trường phát triển:
```bash
npm run dev
```
Truy cập `http://localhost:3000` để trải nghiệm giao diện mới.
