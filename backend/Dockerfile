FROM python:3.11-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONWARNINGS=ignore

# Recon tooling — keeps the original Aptfile contract.
RUN apt-get update -y \
 && apt-get install -y --no-install-recommends \
      bash \
      ca-certificates \
      curl \
      dnsutils \
      gcc \
      jq \
      libc6-dev \
      libcurl4-openssl-dev \
      libssl-dev \
      nmap \
      sqlmap \
      whois \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

COPY backend /app
COPY modules /app/modules
COPY .gf /root/.gf

RUN mkdir -p /app/results \
 && chmod -R 755 /app/modules \
 && find /app/modules -type f \( -name "*.sh" -o -name "clickjacking" -o -name "corstest" \) -exec chmod +x {} +

ENV PYTHONPATH=/app \
    MODULES_DIR=/app/modules \
    RESULTS_DIR=/app/results

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
