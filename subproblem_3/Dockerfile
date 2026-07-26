FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Install PyTorch and dependencies
COPY requirements.txt .

# Install lightweight CPU-only PyTorch first
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install the rest of your requirements with an extended timeout
RUN pip install --default-timeout=1000 --retries 10 --no-cache-dir -r requirements.txt
# Copy source code and model weights (.pt)
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]