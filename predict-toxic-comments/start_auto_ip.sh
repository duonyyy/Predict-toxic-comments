#!/bin/bash

echo "Đang lấy Public IP của VM..."
PUBLIC_IP=$(curl -s ifconfig.me)

if [ -z "$PUBLIC_IP" ]; then
    echo "Không thể lấy được IP. Kiểm tra lại mạng!"
    exit 1
fi

echo "IP hiện tại của bạn là: $PUBLIC_IP"

echo "Đang tự động cập nhật file .env ở thư mục gốc (Kafka)..."
sed -i "s/KAFKA_ADVERTISED_LISTENERS.*/KAFKA_ADVERTISED_LISTENERS = $PUBLIC_IP/g" .env

echo "Đang tự động cập nhật file .env của Frontend..."
sed -i "s|NEXT_PUBLIC_API_URL.*|NEXT_PUBLIC_API_URL=\"http://$PUBLIC_IP:5000\"|g" frontend/.env

echo "Cập nhật thành công! Đang khởi động lại Docker..."
docker compose up -d --force-recreate

echo "====================================================="
echo "Đã xong! Hệ thống đang chạy với IP: $PUBLIC_IP"
echo "Bạn có thể khởi động lại Backend và Frontend ngay bây giờ."
echo "====================================================="
