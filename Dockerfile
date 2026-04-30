# Combined image for Heroku container deployment.
# Builds the React frontend and serves it as static files via FastAPI,
# while the same image is reused (with a different command) for the worker dyno.
FROM node:20-alpine AS web

WORKDIR /web
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY frontend/. .
RUN npm run build


FROM python:3.11-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONWARNINGS=ignore

RUN apt-get update -y \
 && apt-get install -y --no-install-recommends \
      bash ca-certificates curl dnsutils gcc jq libc6-dev \
      libcurl4-openssl-dev libssl-dev nmap sqlmap whois \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

COPY backend /app
COPY modules /app/modules
COPY .gf /root/.gf

# Frontend static bundle served by FastAPI on Heroku (single dyno serves UI + API).
COPY --from=web /web/dist /app/static_web

RUN mkdir -p /app/results \
 && chmod -R 755 /app/modules \
 && find /app/modules -type f \( -name "*.sh" -o -name "clickjacking" -o -name "corstest" \) -exec chmod +x {} +

ENV PYTHONPATH=/app \
    MODULES_DIR=/app/modules \
    RESULTS_DIR=/app/results \
    SERVE_STATIC_WEB=1 \
    STATIC_WEB_DIR=/app/static_web

# Heroku injects $PORT — bind to it; locally defaults to 8000.
CMD ["sh", "-c", "gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120"]
