<h1 align="center">
  <img src="./static/reconator.png" alt="Reconator" width="420">
  <br>
</h1>

<p align="center">
  <img src="https://img.shields.io/badge/release-v2.0-22d3ee">
  <img src="https://img.shields.io/badge/api-FastAPI-009688">
  <img src="https://img.shields.io/badge/web-React%20%2B%20shadcn-0ea5e9">
  <img src="https://img.shields.io/badge/license-GPL3-red">
</p>

**Reconator** is an automated reconnaissance framework. Add a target, the worker
runs ~17 recon modules against it (subdomain enum, dirbrute, JS/link mining, WAF
fingerprint, takeover check, GF triage, and more), and the React dashboard shows
per-module output as it lands.

## Stack

| Layer    | Tech                                                  |
| -------- | ----------------------------------------------------- |
| API      | FastAPI · SQLAlchemy 2 · Alembic · Pydantic v2        |
| Worker   | Python subprocess runner with timeouts + retries      |
| DB       | PostgreSQL 16                                         |
| Web      | React 18 · TypeScript · Tailwind · **shadcn/ui**      |
| Notify   | Telegram (optional)                                   |
| Deploy   | Docker Compose · Heroku container stack               |

## Quickstart — Docker Compose

```bash
git clone https://github.com/gokulapap/Reconator
cd Reconator
cp .env.example .env       # optional: add Telegram keys
docker compose up --build
```

| Service   | URL                       |
| --------- | ------------------------- |
| Web UI    | http://localhost:3000     |
| API docs  | http://localhost:8000/docs |
| Postgres  | localhost:5432            |

The worker auto-picks queued targets every 30s.

## Quickstart — Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/gokulapap/Reconator)

Or via CLI (uses `heroku.yml` container stack — single image serves UI + API,
worker dyno runs the queue):

```bash
heroku create my-reconator --stack=container
heroku addons:create heroku-postgresql:essential-0
heroku config:set TELEGRAM_API_KEY=... TELEGRAM_CHAT_ID=...   # optional
git push heroku master
heroku ps:scale web=1 worker=1
```

## Local development

```bash
# api
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# worker
python -m app.worker

# web
cd frontend && npm install && npm run dev   # proxies /api → :8000
```

## API surface

| Method | Path                                          | Purpose                |
| ------ | --------------------------------------------- | ---------------------- |
| POST   | `/api/v1/targets`                             | Queue a domain         |
| GET    | `/api/v1/targets`                             | List + filter + paginate |
| GET    | `/api/v1/targets/stats`                       | Counts by status       |
| GET    | `/api/v1/targets/{id}`                        | Target + module summary |
| DELETE | `/api/v1/targets/{id}`                        | Cancel / delete        |
| GET    | `/api/v1/targets/{id}/results`                | All module outputs     |
| GET    | `/api/v1/targets/{id}/results/{module}`       | One module's output    |
| GET    | `/api/v1/targets/{id}/results/{module}/download` | Download as `.txt`  |
| GET    | `/api/v1/modules`                             | Available modules      |
| GET    | `/api/v1/health` · `/api/v1/ready`            | Probes                 |

Full OpenAPI spec at `/docs`.

## Configuration

| Env var                          | Default     | Notes                          |
| -------------------------------- | ----------- | ------------------------------ |
| `DATABASE_URL`                   | _composed_  | `postgresql://…` (Heroku-style ok) |
| `TELEGRAM_API_KEY`               | unset       | Disables notifications if blank |
| `TELEGRAM_CHAT_ID`               | unset       |                                |
| `WORKER_POLL_INTERVAL_SECONDS`   | `30`        |                                |
| `MODULE_TIMEOUT_SECONDS`         | `1800`      | Per-module hard timeout        |
| `CORS_ORIGINS`                   | `*`         | Comma-separated                |

## What changed from v1

- Flask → FastAPI; SQL injection vectors removed (parameterized via SQLAlchemy)
- Embedded HTML in Python → React + shadcn/ui dashboard
- Single base64 blob in DB → per-module rows with status/timestamps/errors
- `cron.py` polling loop → proper worker process with graceful shutdown + row locking
- Manual Heroku buildpacks → container stack via `heroku.yml`

## Disclaimer

For authorized testing only. Use on systems you own or have permission to assess.
Released under GPL-3.0.
