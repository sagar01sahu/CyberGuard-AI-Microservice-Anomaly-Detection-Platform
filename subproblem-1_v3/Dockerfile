FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV API_URL=http://backend:8080/api/v1/logs/ingest

CMD ["python", "synthetic_log_generator.py"]