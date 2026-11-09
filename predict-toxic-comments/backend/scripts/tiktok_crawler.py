#!/usr/bin/env python3
"""
TikTok Live Crawler & Kafka Streamer for DS108 Real-Time StreamGuard
Thu thập bình luận TikTok Live và đẩy trực tiếp vào Apache Kafka topic 'comment'.
Hỗ trợ cả chế độ Live thật (TikTokLive) và chế độ giả lập kiểm thử (Simulation).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import random
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [TikTokCrawler]: %(message)s"
)
logger = logging.getLogger("TikTokCrawler")

try:
    from kafka import KafkaProducer
except ImportError:
    logger.error("Chưa cài đặt thư viện 'kafka-python' hoặc 'kafka-python-ng'.")
    sys.exit(1)

try:
    from TikTokLive import TikTokLiveClient
    from TikTokLive.events import (
        CommentEvent,
        ConnectEvent,
        DisconnectEvent,
        LiveEndEvent,
    )
    HAS_TIKTOK_LIVE = True
except ImportError:
    HAS_TIKTOK_LIVE = False
    logger.warning("Chưa cài TikTokLive. Script sẽ hoạt động ở chế độ giả lập (Simulation Mode).")


SAMPLE_COMMENTS = [
    # Safe / Normal
    ("Hôm nay chị live sớm thế ạ ❤️", "Mai Anh", "https://i.pravatar.cc/150?u=maianh"),
    ("Chào mọi người trong phòng live nha!", "Quốc Bảo", "https://i.pravatar.cc/150?u=bao"),
    ("Áo này form rộng hay vừa vậy shop?", "Thuỳ Dương", "https://i.pravatar.cc/150?u=duong"),
    ("Cho em xin mã giảm giá với ạ", "Hoàng Nam", "https://i.pravatar.cc/150?u=nam"),
    ("Follow kênh rồi nha chủ phòng", "Lan Phương", "https://i.pravatar.cc/150?u=phuong"),
    ("Đang xem cùng mẹ nè, vui ghê", "Huy Khánh", "https://i.pravatar.cc/150?u=khanh"),
    ("Chốt đơn mã số 2 nha chị ơi", "Minh Hằng", "https://i.pravatar.cc/150?u=hang"),
    ("Nay hát bài gì thế anh ơi?", "Đức Trí", "https://i.pravatar.cc/150?u=tri"),
    # Explicit (Chửi bới / Công kích thô tục trực tiếp)
    ("Live như cc, nói nhảm tốn thời gian", "Trùm Mõm", "https://i.pravatar.cc/150?u=bad1"),
    ("Con chó này lại lên mạng sủa bậy rồi", "Hacker Lỏ", "https://i.pravatar.cc/150?u=bad2"),
    ("Ngu như bò mà cũng đòi lên dạy đời ai", "Bất Cần", "https://i.pravatar.cc/150?u=bad3"),
    ("Biến mẹ mày đi, nhìn cái mặt hãm vcl", "Chiến Thần", "https://i.pravatar.cc/150?u=bad4"),
    ("Đồ lừa đảo rác rưởi, cút khỏi tóp tóp giùm", "Anti Fan", "https://i.pravatar.cc/150?u=bad5"),
    # Implicit (Mỉa mai / Châm biếm / Khen đểu)
    ("Trí tuệ đỉnh cao thật, phát biểu câu nào là thiên hạ cười bò câu đó", "Gia Cát Dự", "https://i.pravatar.cc/150?u=sarcasm1"),
    ("Cứ ngỡ là chuyên gia ai ngờ lại là diễn viên hài mới nổi", "Khán Giả 4.0", "https://i.pravatar.cc/150?u=sarcasm2"),
    ("Chúc bạn và gia đình gặp nhiều may mắn như những gì bạn đã gây ra nhé", "Người Qua Đường", "https://i.pravatar.cc/150?u=sarcasm3"),
    ("Học hết cấp 1 chưa mà tự tin phát biểu dữ dội vậy ta", "Cư Dân Mạng", "https://i.pravatar.cc/150?u=sarcasm4"),
    ("Bộ não chắc chỉ dùng để trang trí cho cân đối cái đầu thôi nhỉ", "Thánh Soi", "https://i.pravatar.cc/150?u=sarcasm5"),
]


def clean_username(raw: str) -> str:
    clean = raw.strip().lstrip("@")
    if "tiktok.com" in clean:
        parts = clean.split("/")
        for p in parts:
            if p.startswith("@"):
                return p.lstrip("@").strip()
            if "@" in p:
                return p.split("@")[-1].strip()
    return clean.split("?")[0].strip()


class TikTokKafkaStreamer:
    def __init__(
        self,
        username: str,
        stream_id: str,
        kafka_servers: str,
        topic: str,
        simulate: bool = False,
    ):
        self.username = clean_username(username)
        self.stream_id = stream_id or f"tiktok-{self.username}"
        self.kafka_servers = kafka_servers
        self.topic = topic
        self.simulate = simulate
        self.is_running = True
        self.producer = None
        self.client = None

        self._init_kafka()

    def _init_kafka(self):
        try:
            logger.info(f"Kết nối tới Kafka Broker: {self.kafka_servers}...")
            self.producer = KafkaProducer(
                bootstrap_servers=self.kafka_servers.split(","),
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks=1,
            )
            logger.info("✅ Kết nối Kafka thành công!")
        except Exception as e:
            logger.error(f"❌ Không thể kết nối Kafka: {e}")
            sys.exit(1)

    def send_comment_to_kafka(
        self,
        comment_id: str,
        message: str,
        author_id: str,
        author_name: str,
        author_image: str = "",
        published_at: str | None = None,
    ):
        if not self.producer:
            return

        now_str = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        payload = {
            "type": "CHAT",
            "commentId": comment_id,
            "videoId": self.stream_id,
            "message": message,
            "authorId": author_id or f"tiktok-user-{random.randint(1000, 9999)}",
            "authorName": author_name or "TikToker",
            "authorImage": author_image,
            "publishedAt": published_at or now_str,
            "platform": "tiktok",
        }

        try:
            self.producer.send(self.topic, payload)
            logger.info(f"Đã đẩy comment vào Kafka [{self.stream_id}]: {author_name}: {message[:40]}")
        except Exception as e:
            logger.error(f"Lỗi khi gửi vào Kafka: {e}")

    async def run_live(self):
        if not HAS_TIKTOK_LIVE or self.simulate:
            await self.run_simulation()
            return

        logger.info(f"Đang kết nối TikTok LIVE: @{self.username}...")
        self.client = TikTokLiveClient(unique_id=f"@{self.username}")

        @self.client.on(ConnectEvent)
        async def on_connect(event: ConnectEvent):
            room_id = getattr(self.client, "room_id", "")
            logger.info(f"✅ Đã kết nối thành công tới TikTok LIVE @{self.username} (Room ID: {room_id})")

        @self.client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            if not self.is_running:
                return

            text = str(getattr(event, "comment", "") or "").strip()
            if not text:
                return

            msg_id = getattr(event, "msg_id", None) or f"{time.time_ns()}"
            user = getattr(event, "user", None)
            author_id = str(getattr(user, "unique_id", "") or getattr(user, "id", "") or "tiktok_user")
            author_name = str(getattr(user, "nickname", "") or getattr(user, "unique_id", "") or "TikTok User")
            
            # Avatar
            author_image = ""
            avatar_obj = getattr(user, "avatar", None)
            if avatar_obj and hasattr(avatar_obj, "urls") and avatar_obj.urls:
                author_image = avatar_obj.urls[0]

            self.send_comment_to_kafka(
                comment_id=f"tiktok-{msg_id}",
                message=text,
                author_id=author_id,
                author_name=author_name,
                author_image=author_image,
            )

        @self.client.on(DisconnectEvent)
        async def on_disconnect(event: DisconnectEvent):
            logger.warning(f"⚠️ Mất kết nối tới TikTok LIVE @{self.username}.")

        @self.client.on(LiveEndEvent)
        async def on_live_end(event: LiveEndEvent):
            logger.info(f"🛑 TikTok LIVE @{self.username} đã kết thúc.")
            self.is_running = False

        try:
            await self.client.connect()
        except Exception as e:
            logger.warning(
                f"⚠️ Không thể kết nối trực tiếp với TikTok LIVE @{self.username}: {e}\n"
                f"🔄 Tự động chuyển sang Chế độ Giả lập (Simulation Mode) để tiếp tục kiểm thử luồng..."
            )
            await self.run_simulation()

    async def run_simulation(self):
        logger.info(f"🚀 Bắt đầu chế độ Giả lập luồng bình luận TikTok Live cho @{self.username}...")
        comment_idx = 1
        while self.is_running:
            # Chọn ngẫu nhiên một bình luận
            msg_tuple = random.choice(SAMPLE_COMMENTS)
            text, author_name, author_image = msg_tuple
            comment_id = f"tiktok-sim-{int(time.time() * 1000)}-{comment_idx}"
            author_id = f"tiktok-user-{abs(hash(author_name)) % 10000}"

            self.send_comment_to_kafka(
                comment_id=comment_id,
                message=text,
                author_id=author_id,
                author_name=author_name,
                author_image=author_image,
            )
            comment_idx += 1

            # Đợi ngẫu nhiên 1.5 - 3.5 giây giữa các comment
            await asyncio.sleep(random.uniform(1.5, 3.5))

    def stop(self):
        logger.info("Nhận lệnh dừng TikTok Streamer...")
        self.is_running = False
        if self.client and hasattr(self.client, "disconnect"):
            try:
                asyncio.create_task(self.client.disconnect())
            except Exception:
                pass
        if self.producer:
            self.producer.flush()
            self.producer.close()


def main():
    parser = argparse.ArgumentParser(description="TikTok Live Streamer to Kafka")
    parser.add_argument("--username", required=True, help="TikTok @username or live URL")
    parser.add_argument("--stream_id", default="", help="Stream Identifier (default: tiktok-<username>)")
    parser.add_argument(
        "--kafka",
        default=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        help="Kafka bootstrap servers",
    )
    parser.add_argument(
        "--topic",
        default=os.getenv("KAFKA_TOPIC", "comment"),
        help="Kafka topic",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Force simulation mode instead of connecting to real TikTok",
    )

    args = parser.parse_args()

    streamer = TikTokKafkaStreamer(
        username=args.username,
        stream_id=args.stream_id,
        kafka_servers=args.kafka,
        topic=args.topic,
        simulate=args.simulate,
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def handle_signal(sig, frame):
        streamer.stop()
        loop.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        loop.run_until_complete(streamer.run_live())
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        streamer.stop()
        loop.close()
        logger.info("TikTok Crawler đã dừng an toàn.")


if __name__ == "__main__":
    main()
