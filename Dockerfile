FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create storage dirs
RUN mkdir -p storage

# Accept project args via env vars, run in auto-approve mode
ENV PROJECT_NAME=loop_test
ENV SPEC_TEXT="Build a simple REST API health check endpoint"
ENV AUTO_APPROVE=true

CMD ["sh", "-c", "python main.py --project \"$PROJECT_NAME\" --spec \"$SPEC_TEXT\" --auto-approve"]
