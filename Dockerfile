# ─── Stage 1: Build Python dependencies ──────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install Python dependencies (orchestrator + frontend)
COPY requirements.txt ./
COPY frontend/requirements.txt frontend-requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r frontend-requirements.txt && \
    rm frontend-requirements.txt

# ─── Stage 2: Runtime — Python + nginx ─────────────────────────
FROM python:3.12-slim

# Install nginx + system deps + Playwright Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    fonts-liberation libasound2 libatk-bridge2.0-0 libcups2 libdrm2 \
    libgbm1 libnss3 libx11-6 libxcomposite1 libxcursor1 libxdamage1 \
    libxfixes3 libxrandr2 libxshmfence1 libxtst6 libpango-1.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m playwright install chromium

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy all application code (orchestrator + frontend)
COPY . .

# Copy static frontend files into nginx document root
COPY frontend/static/ /usr/share/nginx/html/
RUN chmod -R 755 /usr/share/nginx/html/

# Configure nginx
COPY frontend/nginx/nginx.conf /etc/nginx/sites-available/default
RUN rm -f /etc/nginx/sites-enabled/default && \
    ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/

# Create writable build directory for SQLite checkpoint persistence
RUN mkdir -p /app/build

# Expose all three ports: nginx, uvicorn, health server
EXPOSE 80 8011 8081

# Environment defaults
ENV PYTHONPATH=/app
ENV PROJECT_NAME=loop_test
ENV SPEC_TEXT="Build a simple REST API health check endpoint"
ENV AUTO_APPROVE=false
ENV OBSERVABILITY_PORT=8081

# Entrypoint starts: nginx (:80), uvicorn (:8011), health server (:8081)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]
