FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Default command to run the benchmark
CMD ["python", "src/main.py", "--config", "bench_config.yaml"]
