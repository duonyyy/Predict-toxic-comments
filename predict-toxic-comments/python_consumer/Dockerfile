FROM python:3.11-slim-bookworm

WORKDIR /app

# Cài đặt curl và build cơ bản nếu cần
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY consumer.py .

CMD ["python", "-u", "consumer.py"]

