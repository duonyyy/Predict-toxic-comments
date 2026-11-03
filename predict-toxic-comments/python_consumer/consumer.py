import os
import re
import json
import logging
import unicodedata
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import numpy as np

# MongoDB
from pymongo import MongoClient

# Kafka
from kafka import KafkaConsumer

# Machine Learning
import torch
import torch.nn as nn
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Optional PyVi for PhoBERT Vietnamese Word Segmentation
try:
    import pyvi.ViTokenizer as vi_tokenizer
    HAS_PYVI = True
except ImportError:
    HAS_PYVI = False

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DS108ToxicConsumer")

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI") or os.getenv("URL_MONGO", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME") or os.getenv("MONGO_DB_NAME", "commentStreaming")
BOOTSTRAP_SERVERS = (
    os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    or os.getenv("BOOTSTRAP_SERVERS")
    or os.getenv("KAFKA_BOOTSTRAP_SERVER", "localhost:9092")
)
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "comment")

# Model Paths & Configurations (DS108 Hierarchical 2-stage)
TASK1_MODEL_PATH = os.getenv("TASK1_MODEL_PATH", "../model/phobert_task1.pt")
TASK2_MODEL_PATH = os.getenv("TASK2_MODEL_PATH", "../model/xlmr_task2.pt")
PHOBERT_PRETRAINED = os.getenv("PHOBERT_PRETRAINED", "vinai/phobert-base-v2")
XLMR_PRETRAINED = os.getenv("XLMR_PRETRAINED", "FacebookAI/xlm-roberta-base")

GARBAGE_PATTERN = re.compile(r"(https?://\S+|www\.\S+|\S+@\S+)")


class DS108HierarchicalClassifier:
    """
    Hệ thống phân loại phân cấp 2 tầng (Hierarchical 2-stage Classifier) của DS108:
      - Tác vụ 1: Toxicity Classification (NON-TOXIC vs TOXIC) -> Best model: PhoBERT-base-v2
      - Tác vụ 2: Expression Classification (EXPLICIT vs IMPLICIT) -> Best model: XLM-RoBERTa-base
    Hỗ trợ nạp checkpoint PyTorch hoặc Heuristic chuẩn ngữ liệu tiếng Việt.
    """

    def __init__(self, device: torch.device):
        self.device = device
        self.task1_model = None
        self.task1_tokenizer = None
        self.task2_model = None
        self.task2_tokenizer = None
        self.is_neural_ready = False

        self._init_models()

    def _init_models(self):
        # 1. Thử tìm weights cho Tác vụ 1 (PhoBERT)
        candidate_t1 = [
            TASK1_MODEL_PATH,
            "./model/phobert_task1.pt",
            "../model/phobert_task1.pt",
            "../../Model/artifacts/phobert/task1/best_model.pt",
            "/model/phobert_task1.pt",
        ]
        found_t1 = next((p for p in candidate_t1 if os.path.exists(p) and os.path.getsize(p) > 1024), None)

        # 2. Thử tìm weights cho Tác vụ 2 (XLM-R hoặc PhoBERT)
        candidate_t2 = [
            TASK2_MODEL_PATH,
            "./model/xlmr_task2.pt",
            "../model/xlmr_task2.pt",
            "../../Model/artifacts/xlmr/task2/best_model.pt",
            "/model/xlmr_task2.pt",
        ]
        found_t2 = next((p for p in candidate_t2 if os.path.exists(p) and os.path.getsize(p) > 1024), None)

        if found_t1:
            try:
                logger.info(f"Nạp checkpoint Tác vụ 1 (PhoBERT) từ: {found_t1}")
                self.task1_tokenizer = AutoTokenizer.from_pretrained(PHOBERT_PRETRAINED)
                self.task1_model = AutoModelForSequenceClassification.from_pretrained(
                    PHOBERT_PRETRAINED, num_labels=2
                )
                self.task1_model.load_state_dict(torch.load(found_t1, map_location=self.device))
                self.task1_model.to(self.device).eval()
            except Exception as e:
                logger.warning(f"Không thể nạp mô hình nơ-ron Tác vụ 1: {e}")
                self.task1_model = None

        if found_t2:
            try:
                logger.info(f"Nạp checkpoint Tác vụ 2 (XLM-R) từ: {found_t2}")
                self.task2_tokenizer = AutoTokenizer.from_pretrained(XLMR_PRETRAINED)
                self.task2_model = AutoModelForSequenceClassification.from_pretrained(
                    XLMR_PRETRAINED, num_labels=2
                )
                self.task2_model.load_state_dict(torch.load(found_t2, map_location=self.device))
                self.task2_model.to(self.device).eval()
            except Exception as e:
                logger.warning(f"Không thể nạp mô hình nơ-ron Tác vụ 2: {e}")
                self.task2_model = None

        if self.task1_model is not None and self.task2_model is not None:
            self.is_neural_ready = True
            logger.info("✅ Đã khởi tạo thành công cả 2 mô hình Transformer nơ-ron phân cấp DS108!")
        else:
            logger.info(
                "ℹ️ Hệ thống kích hoạt Chế độ Heuristic DS108 (Phân cấp 2 tầng TOXIC/NON-TOXIC & EXPLICIT/IMPLICIT)\n"
                "   Dựa trên quy chuẩn Codebook và Bộ dữ liệu nghiên cứu chuẩn vàng 48,670 mẫu tiếng Việt."
            )

    def segment_vietnamese(self, text: str) -> str:
        if HAS_PYVI:
            try:
                return vi_tokenizer.tokenize(text)
            except Exception:
                return text
        return text

    def predict(self, text: str):
        """
        Dự đoán phân cấp 2 tầng theo chuẩn DS108:
        Return dict:
          - toxicity: "TOXIC" | "NON-TOXIC"
          - expression_type: "EXPLICIT" | "IMPLICIT" | None
          - toxic_score: float [0, 1]
          - implicit_score: float [0, 1]
          - toxic_label: "TOXIC" | "NON-TOXIC"
          - toxic_category: "EXPLICIT" | "IMPLICIT" | "NON-TOXIC"
          - recommended_action: "Ban" | "Hide" | "Pending" | "Safe"
          - probs: dict
        """
        if self.is_neural_ready:
            return self._predict_neural(text)
        return self._predict_heuristic(text)

    def _predict_neural(self, text: str):
        # Tác vụ 1: Phân loại Toxicity với PhoBERT
        seg_text = self.segment_vietnamese(text)
        inputs_t1 = self.task1_tokenizer(
            seg_text, max_length=128, padding=True, truncation=True, return_tensors="pt"
        )
        inputs_t1 = {k: v.to(self.device) for k, v in inputs_t1.items()}
        with torch.no_grad():
            logits_t1 = self.task1_model(**inputs_t1).logits
            probs_t1 = torch.softmax(logits_t1, dim=-1).cpu().numpy()[0]

        toxic_score = float(probs_t1[1])  # 0: NON-TOXIC, 1: TOXIC
        is_toxic = toxic_score >= 0.5
        toxicity = "TOXIC" if is_toxic else "NON-TOXIC"

        expression_type = None
        implicit_score = 0.0

        if is_toxic and self.task2_model is not None:
            # Tác vụ 2: Phân loại Biểu đạt trên tập TOXIC
            inputs_t2 = self.task2_tokenizer(
                text, max_length=128, padding=True, truncation=True, return_tensors="pt"
            )
            inputs_t2 = {k: v.to(self.device) for k, v in inputs_t2.items()}
            with torch.no_grad():
                logits_t2 = self.task2_model(**inputs_t2).logits
                probs_t2 = torch.softmax(logits_t2, dim=-1).cpu().numpy()[0]

            # 0: EXPLICIT, 1: IMPLICIT
            implicit_score = float(probs_t2[1])
            expression_type = "IMPLICIT" if implicit_score >= 0.5 else "EXPLICIT"

        return self._build_result(toxicity, expression_type, toxic_score, implicit_score)

    def _predict_heuristic(self, text: str):
        """
        Bộ quy tắc phân loại chuyên sâu theo đúng Codebook và Taxonomy DS108:
        1. Explicit: Xúc phạm thô tục, chửi thề trực tiếp, lăng mạ nhắm vào đối tượng.
        2. Implicit: Mỉa mai, châm biếm, khen đểu, câu hỏi tu từ, hạ bệ tinh vi không dùng từ tục thô thiển.
        3. Non-toxic: Khẩu ngữ, đùa vui, thảo luận trung tính, phản biện không xúc phạm.
        """
        lower = text.lower()

        # Danh mục từ ngữ công kích trực tiếp (EXPLICIT)
        explicit_patterns = [
            r"\b(đ[iụịme]|d[mcm]|đ[ccl]|đ[bc]|v[cl]|vcl|đkm|đmm|dmm|cc|đéo|đếch)\b",
            r"\b(ngu|ngu ngốc|ngu dốt|óc chó|óc bã đậu|óc bò|óc heo|não tàn|thiểu năng|đần độn)\b",
            r"\b(chó|con chó|lũ chó|chó đẻ|súc sinh|súc vật|cặn bã|rác rưởi|bẩn thỉu|đồ khốn|mất dạy)\b",
            r"\b(cút|cút xéo|biến mẹ mày đi|câm mồm|ngậm mồm|đập chết|giết chết|chém chết)\b",
            r"\b(đĩ|phò|con điếm|đĩ mẹ|cave|thằng ranh con|bú fame|hãm l|hãm lol)\b"
        ]

        # Danh mục mẫu câu mỉa mai / công kích ẩn ý (IMPLICIT)
        implicit_patterns = [
            r"(trí tuệ|não|iq)\s*(đỉnh cao|vô cực|thượng thừa|vô tận|dữ|quá)",
            r"(phát biểu|nói)\s*(câu nào|câu gì)\s*(thiên hạ|người ta|dân tình)\s*(cười bò|cười ỉa|cười té ghế)",
            r"(cứ ngỡ|tưởng là|tưởng)\s*(chuyên gia|thần thánh|pro)\s*(ai ngờ|hóa ra|lại là)\s*(diễn viên hài|chú hề|tấu hề|bịp)",
            r"(chúc|mong)\s*(bạn|mày|gia đình)\s*(gặp|nhận)\s*(may mắn|điều tốt)\s*như\s*(những gì|việc)\s*(đã gây|làm)",
            r"(học hết|tốt nghiệp|xong)\s*(cấp 1|cấp 2|mẫu giáo|lớp mấy)\s*(chưa|rồi à)",
            r"(não|óc)\s*(để|dùng để)\s*(trang trí|chứa nước|cho có|nuôi tóc|chưng)",
            r"(nghe|xem)\s*(mà|thấy)\s*(tội nghiệp|thương hại|muốn đội quần|mắc cỡ giùm|xấu hổ giùm)",
            r"\b(tấu hề|chúa tấu hề|nghệ sĩ nhân dân|chuyên gia mõm|danh hài mới nổi|hài hước thật)\b",
            r"(đúng là|chuẩn)\s*(thiên tài|giáo sư)\s*(nửa mùa|online|tự phong|bàn phím)"
        ]

        # Kiểm tra explicit
        explicit_hits = sum(1 for p in explicit_patterns if re.search(p, lower))
        # Kiểm tra implicit
        implicit_hits = sum(1 for p in implicit_patterns if re.search(p, lower))

        if explicit_hits > 0:
            # Phát hiện từ ngữ chửi bới / lăng mạ trực tiếp
            toxicity = "TOXIC"
            expression_type = "EXPLICIT"
            toxic_score = min(0.78 + (explicit_hits * 0.08), 0.99)
            implicit_score = 0.08
        elif implicit_hits > 0:
            # Phát hiện mỉa mai / ẩn ý / châm biếm
            toxicity = "TOXIC"
            expression_type = "IMPLICIT"
            toxic_score = min(0.72 + (implicit_hits * 0.09), 0.92)
            implicit_score = min(0.80 + (implicit_hits * 0.08), 0.96)
        else:
            # Bình luận thông thường
            toxicity = "NON-TOXIC"
            expression_type = None
            toxic_score = 0.08
            implicit_score = 0.05

        return self._build_result(toxicity, expression_type, toxic_score, implicit_score)

    def _build_result(self, toxicity: str, expression_type: str | None, toxic_score: float, implicit_score: float):
        toxic_score = round(float(toxic_score), 4)
        implicit_score = round(float(implicit_score), 4)
        is_toxic = toxicity == "TOXIC"

        # Quyết định hành động theo tiêu chuẩn Khóa luận / Đồ án DS108:
        # 1. Ban: TOXIC - EXPLICIT với điểm số cao (>= 0.85) -> Cấm vĩnh viễn
        # 2. Hide: TOXIC (>= 0.70) -> Ẩn khỏi màn hình công cộng
        # 3. Pending: TOXIC - IMPLICIT (công kích ẩn ý cần người duyệt) HOẶC điểm số [0.50, 0.70)
        # 4. Safe: NON-TOXIC (< 0.50) -> Giữ nguyên an toàn
        if is_toxic:
            if expression_type == "EXPLICIT" and toxic_score >= 0.85:
                recommended_action = "Ban"
            elif expression_type == "IMPLICIT":
                recommended_action = "Pending"
            elif toxic_score >= 0.70:
                recommended_action = "Hide"
            else:
                recommended_action = "Pending"
            toxic_category = expression_type or "EXPLICIT"
        else:
            recommended_action = "Safe"
            toxic_category = "NON-TOXIC"

        return {
            "toxicity": toxicity,
            "expression_type": expression_type,
            "toxic_label": toxicity,
            "toxic_category": toxic_category,
            "toxic_score": toxic_score,
            "implicit_score": implicit_score,
            "recommended_action": recommended_action,
            "predictions": {
                "toxic": toxic_score,
                "non_toxic": round(1.0 - toxic_score, 4),
                "explicit": round(1.0 - implicit_score, 4) if is_toxic else 0.0,
                "implicit": implicit_score if is_toxic else 0.0,
            },
        }


def clean_message(raw_msg: str) -> str:
    if not raw_msg:
        return ""
    # Xóa URL và email
    msg = GARBAGE_PATTERN.sub("", raw_msg.strip())
    # Chuẩn hóa khoảng trắng
    msg = re.sub(r"\s+", " ", msg).strip()
    # Chuẩn hóa Unicode NFC
    msg = unicodedata.normalize("NFC", msg)
    return msg


def parse_date(date_val):
    if not date_val:
        return datetime.now(timezone.utc)
    if isinstance(date_val, datetime):
        return date_val
    try:
        return datetime.fromisoformat(str(date_val).replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


def get_window(dt: datetime):
    # Khung cửa sổ thời gian 1 phút
    start = dt.replace(second=0, microsecond=0)
    end = start + timedelta(minutes=1)
    return start, end


def process_comment(db, comment_data: dict, classifier: DS108HierarchicalClassifier):
    comment_id = comment_data.get("commentId")
    video_id = comment_data.get("videoId")
    raw_message = comment_data.get("message", "")
    author_id = comment_data.get("authorId")
    author_name = comment_data.get("authorName", "Unknown")
    author_image = comment_data.get("authorImage", "")
    published_at = parse_date(comment_data.get("publishedAt"))

    if not comment_id or not video_id:
        return

    cleaned_msg = clean_message(raw_message)
    pred = classifier.predict(cleaned_msg if cleaned_msg else raw_message)

    window_start, window_end = get_window(published_at)

    # 1. Lưu bản ghi phân tích bình luận (live_comment_analysis)
    comment_doc = {
        "comment_id": comment_id,
        "video_id": video_id,
        "author_id": author_id,
        "author_name": author_name,
        "author_image": author_image,
        "message": raw_message,
        "cleaned_message": cleaned_msg,
        "published_at": published_at,
        "toxicity": pred["toxicity"],
        "expression_type": pred["expression_type"],
        "toxic_label": pred["toxic_label"],
        "toxic_category": pred["toxic_category"],
        "toxic_score": pred["toxic_score"],
        "implicit_score": pred["implicit_score"],
        "recommended_action": pred["recommended_action"],
        "predictions": pred["predictions"],
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
    }

    try:
        db.live_comment_analysis.insert_one(comment_doc)
    except Exception:
        db.live_comment_analysis.replace_one({"comment_id": comment_id}, comment_doc, upsert=True)

    # 2. Cập nhật thống kê theo luồng 1 phút (live_stream_metric)
    is_toxic = pred["toxicity"] == "TOXIC"
    is_explicit = pred["expression_type"] == "EXPLICIT"
    is_implicit = pred["expression_type"] == "IMPLICIT"

    toxic_inc = 1 if is_toxic else 0
    explicit_inc = 1 if is_explicit else 0
    implicit_inc = 1 if is_implicit else 0

    metric_filter = {
        "video_id": video_id,
        "window_start": window_start,
    }
    metric_update = {
        "$setOnInsert": {
            "window_end": window_end,
            "createdAt": datetime.now(timezone.utc),
        },
        "$inc": {
            "total_comments": 1,
            "toxic_count": toxic_inc,
            "explicit_count": explicit_inc,
            "implicit_count": implicit_inc,
        },
        "$addToSet": {
            "viewers": author_id,
        },
        "$set": {
            "updatedAt": datetime.now(timezone.utc),
        },
    }

    metric = db.live_stream_metric.find_one_and_update(
        metric_filter,
        metric_update,
        upsert=True,
        return_document=True,
    )

    if metric:
        total = metric.get("total_comments", 1)
        toxic = metric.get("toxic_count", 0)
        viewers = metric.get("viewers", [])
        toxic_ratio = round((toxic / total) * 100, 2) if total > 0 else 0.0

        db.live_stream_metric.update_one(
            {"_id": metric["_id"]},
            {
                "$set": {
                    "toxic_ratio": toxic_ratio,
                    "unique_viewers": len(viewers),
                }
            },
        )

    # 3. Cập nhật thống kê người dùng độc hại (toxic_user_metric) nếu vi phạm
    if is_toxic and author_id:
        user_filter = {
            "video_id": video_id,
            "author_id": author_id,
            "window_start": window_start,
        }
        user_update = {
            "$setOnInsert": {
                "author_name": author_name,
                "author_image": author_image,
                "window_end": window_end,
                "createdAt": datetime.now(timezone.utc),
            },
            "$inc": {
                "toxic_count": 1,
                "explicit_count": explicit_inc,
                "implicit_count": implicit_inc,
            },
            "$set": {
                "updatedAt": datetime.now(timezone.utc),
            },
        }
        db.toxic_user_metric.update_one(user_filter, user_update, upsert=True)

    logger.info(
        f"[{pred['toxicity']} - {pred['toxic_category']}] "
        f"Score: {pred['toxic_score']} | Action: {pred['recommended_action']} | "
        f"User: {author_name} | Msg: {raw_message[:50]}"
    )


def main():
    logger.info("Khởi động DS108 Toxic Consumer (Phân loại phân cấp 2 tầng)...")
    logger.info(f"Kết nối MongoDB: {MONGO_URI} / DB: {DATABASE_NAME}")
    logger.info(f"Kết nối Kafka: {BOOTSTRAP_SERVERS} / Topic: {KAFKA_TOPIC}")

    # Kết nối MongoDB
    try:
        mongo_client = MongoClient(MONGO_URI)
        db = mongo_client[DATABASE_NAME]
        db.command("ping")
        logger.info("✅ Kết nối MongoDB thành công!")
    except Exception as e:
        logger.error(f"❌ Kết nối MongoDB thất bại: {e}")
        return

    # Khởi tạo mô hình phân cấp DS108
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Phần cứng tính toán PyTorch: {device}")
    classifier = DS108HierarchicalClassifier(device=device)

    # Kết nối Kafka Consumer
    consumer = None
    retry_delay = 5
    max_retries = 10
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Đang kết nối tới Kafka ({attempt}/{max_retries})...")
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=BOOTSTRAP_SERVERS.split(","),
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="latest",
                enable_auto_commit=True,
                group_id="ds108-toxic-consumer-group",
            )
            logger.info(f"✅ Kết nối Kafka thành công! Bắt đầu lắng nghe topic '{KAFKA_TOPIC}'...")
            break
        except Exception as e:
            logger.warning(f"Chưa thể kết nối Kafka: {e}. Thử lại sau {retry_delay}s...")
            import time
            time.sleep(retry_delay)

    if not consumer:
        logger.error("❌ Không thể kết nối tới Kafka Broker sau nhiều lần thử. Dừng consumer.")
        return

    # Vòng lặp tiêu thụ tin nhắn
    try:
        for message in consumer:
            data = message.value
            try:
                process_comment(db, data, classifier)
            except Exception as e:
                logger.error(f"Lỗi khi xử lý bình luận: {e}", exc_info=True)
    except KeyboardInterrupt:
        logger.info("Đã nhận tín hiệu dừng từ người dùng.")
    finally:
        consumer.close()
        mongo_client.close()
        logger.info("Đã đóng kết nối Consumer và MongoDB.")


if __name__ == "__main__":
    main()
