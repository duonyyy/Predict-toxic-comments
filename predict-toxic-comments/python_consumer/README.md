# Python Toxic Comment Consumer (Bản thay thế nhẹ cho Spark)

Dịch vụ này thay thế hoàn toàn **Apache Spark** trong dự án:
- Tiêu thụ trực tiếp luồng bình luận từ Kafka topic `comment`.
- Tiền xử lý văn bản (làm sạch URL, email, chuẩn hóa khoảng trắng và Unicode NFC).
- Suy luận phân loại độc hại (ViSoBERT) qua PyTorch.
- Tính toán window 1 phút và ghi dữ liệu đồng thời vào 3 collection MongoDB:
  - `live_comment_analysis`
  - `live_stream_metric`
  - `toxic_user_metric`
- Tiết kiệm hơn **3 - 4GB RAM** so với cụm Spark + JVM.

---

## 🛠 Cách 1: Chạy trực tiếp bằng Python trên máy (Nhanh nhất & Nhẹ nhất)

1. Cài đặt các thư viện cần thiết:
```bash
cd python_consumer
pip install -r requirements.txt
```

2. Tạo hoặc cấu hình file `.env` (hoặc để mặc định kết nối localhost):
```env
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=commentStreaming
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=comment
MODEL_PATH=../model/visobert_toxic.pt
```

3. Khởi chạy:
```bash
python consumer.py
```

---

## 🐳 Cách 2: Chạy cùng Docker Compose

Chạy file cấu hình rút gọn [docker-compose-light.yml](../docker-compose-light.yml):

```bash
docker compose -f docker-compose-light.yml up -d
```
Lệnh này sẽ khởi động:
- 1 Broker Kafka (thay vì 3 broker)
- 1 Redis
- 1 Python Consumer (giới hạn tối đa 1GB RAM thay vì 5GB RAM của Spark)

