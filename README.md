<h1 align="center">
  <img src="./static/reconator.png" alt="Reconator" width="420">
  <br>
</h1>

<p align="center">
  <img src="https://img.shields.io/badge/release-v2.1-22d3ee">
  <img src="https://img.shields.io/badge/api-FastAPI-009688">
  <img src="https://img.shields.io/badge/web-React%20%2B%20shadcn-0ea5e9">
  <img src="https://img.shields.io/badge/license-GPL3-red">
</p>

**Reconator** is an automated reconnaissance framework. Add a target — alone or
in bulk — and the worker runs ~17 recon modules against it (subdomain enum,
dirbrute, JS/link mining, WAF fingerprint, takeover check, GF triage, and more).
The dashboard shows per-module output as it lands.

## Stack

| Layer    | Tech                                                                |
| -------- | ------------------------------------------------------------------- |
| API      | FastAPI · SQLAlchemy 2 · Alembic · Pydantic v2                      |
| Worker   | Python subprocess runner with timeouts + cancellation               |
| DB       | PostgreSQL 16                                                       |
| Web      | React 18 · TypeScript · Tailwind · **shadcn/ui** · light/dark theme |
| Auth     | API key (`X-API-Key`) on writes; open in dev                        |
| Notify   | Telegram + generic / Slack / Discord webhook                        |
| Observe  | JSON logs · request IDs · Prometheus `/metrics` · optional Sentry   |
| Deploy   | Docker Compose · Heroku container stack                             |

## Quickstart — Docker Compose

```bash
git clone https://github.com/gokulapap/Reconator
cd Reconator
cp .env.example .env       # optional: add Telegram / webhook keys / API key
docker compose up --build
```

| Service   | URL                        |
| --------- | -------------------------- |
| Web UI    | http://localhost:3000      |
| API docs  | http://localhost:8000/docs |
| Metrics   | http://localhost:8000/api/v1/metrics |

## Quickstart — Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/gokulapap/Reconator)

Or via CLI (uses `heroku.yml` container stack — single image serves UI + API,
worker dyno runs the queue):

```bash
heroku create my-reconator --stack=container
heroku addons:create heroku-postgresql:essential-0
heroku config:set ADMIN_API_KEY=$(openssl rand -hex 32)   # recommended
heroku config:set TELEGRAM_API_KEY=... TELEGRAM_CHAT_ID=...   # optional
git push heroku master
heroku ps:scale web=1 worker=1
```

## Local development

```bash
# api
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# worker (separate shell)
python -m app.worker

# web (separate shell)
cd frontend && npm install && npm run dev   # proxies /api → :8000

# tests + lint
cd backend && pytest && ruff check .
```

## Features

- **Bulk add** — paste up to 500 domains; per-row error / conflict report
- **Tags + filtering** — tag targets, filter the listing by tag
- **Module selection** — schedule only the modules you want per target
- **Cancel + rescan** — stop a running target between modules; one-click rescan
- **Per-module results** — each check's output is its own row, with status, timing, errors
- **In-output search + highlight** — filter giant subdomain dumps in place
- **CSV / JSON export** — pull the whole queue out of the API
- **Live dashboard** — counts, average scan duration, recent activity
- **Optional API-key auth** — set `ADMIN_API_KEY`, all mutations require `X-API-Key`
- **Rate limiting** — slowapi caps writes (defaults: 20/min single, 5/min bulk)
- **Prometheus metrics** — request rate, latency, scan counts, queue depth
- **Telegram + webhook fan-out** — notifier abstraction, both can run together
- **Light + dark UI** — preference stored per browser

## API surface

| Method | Path                                             | Auth | Purpose                |
| ------ | ------------------------------------------------ | ---- | ---------------------- |
| GET    | `/api/v1/targets`                                | —    | List + filter (status, search, tag) |
| POST   | `/api/v1/targets`                                | ✓    | Queue a domain         |
| POST   | `/api/v1/targets/bulk`                           | ✓    | Queue many at once     |
| GET    | `/api/v1/targets/stats`                          | —    | Counts + avg duration  |
| GET    | `/api/v1/targets/export?format=csv\|json`        | —    | Bulk export            |
| GET    | `/api/v1/targets/{id}`                           | —    | Detail + module summary |
| DELETE | `/api/v1/targets/{id}`                           | ✓    | Delete (or cancel if running) |
| POST   | `/api/v1/targets/{id}/cancel`                    | ✓    | Cancel queued / running |
| POST   | `/api/v1/targets/{id}/rescan`                    | ✓    | Re-queue with same tags / modules |
| GET    | `/api/v1/targets/{id}/results`                   | —    | All module outputs     |
| GET    | `/api/v1/targets/{id}/results/{module}`          | —    | One module's output    |
| GET    | `/api/v1/targets/{id}/results/{module}/download` | —    | `.txt` download        |
| GET    | `/api/v1/modules`                                | —    | Available modules      |
| GET    | `/api/v1/system/info`                            | —    | Version + auth + notifier status |
| POST   | `/api/v1/system/test-notify`                     | ✓    | Fire a test notification |
| GET    | `/api/v1/health` · `/ready` · `/metrics`         | —    | Probes + Prometheus    |

OpenAPI at `/docs`.

## Configuration

| Env var                          | Default     | Notes                          |
| -------------------------------- | ----------- | ------------------------------ |
| `DATABASE_URL`                   | _composed_  | `postgresql://…` (Heroku-style ok) |
| `ADMIN_API_KEY`                  | unset       | When set, mutations require `X-API-Key` |
| `RATE_LIMIT_WRITES`              | `20/minute` | slowapi expression             |
| `RATE_LIMIT_BULK`                | `5/minute`  |                                |
| `TELEGRAM_API_KEY` / `_CHAT_ID`  | unset       | Disables telegram if blank     |
| `WEBHOOK_URL` / `WEBHOOK_KIND`   | unset / `generic` | `generic` \| `slack` \| `discord` |
| `SENTRY_DSN`                     | unset       | Enables Sentry if set          |
| `WORKER_POLL_INTERVAL_SECONDS`   | `30`        |                                |
| `MODULE_TIMEOUT_SECONDS`         | `1800`      | Per-module hard timeout        |
| `CORS_ORIGINS`                   | `*`         | Comma-separated                |

## What changed from v1

- Flask → FastAPI; SQL injection vectors gone (parameterized SQLAlchemy)
- Embedded HTML → React + shadcn/ui dashboard
- Single base64 blob in DB → per-module rows with status / timestamps / errors
- `cron.py` polling loop → worker with row-locking, graceful shutdown, cancellation
- Manual Heroku buildpacks → container stack via `heroku.yml`
- Added: API-key auth, rate limiting, request IDs, Prometheus, Sentry hook,
  bulk import, tags, rescan, cancel, webhook notifier, CSV/JSON export

## Disclaimer

For authorized testing only. Use on systems you own or have permission to assess.
Released under GPL-3.0.
