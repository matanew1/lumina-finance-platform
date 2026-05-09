# Lumina Finance Platform

A finance platform skeleton with a FastAPI backend, SQLAlchemy models, PostgreSQL/SQLite database support, Swagger UI, and a simple React frontend.

Transaction upload ingestion, validation, client listing, FIFO position calculation, violation detection, and analytics are implemented.

## Tech Stack

- Backend: Python, FastAPI, SQLAlchemy, pandas
- Database: PostgreSQL with Docker Compose; SQLite is also supported by changing `DATABASE_URL`
- Frontend: React with Vite
- API docs: Swagger UI through FastAPI

## Project Structure

```text
backend/
  db/
    database.py    singleton database service, sessions, and init helpers
    models/        domain-grouped SQLAlchemy models
    repositories/  domain-grouped database access layer
  controllers/     feature-based FastAPI controller packages
  samples/         sample input files
  schemas/         Pydantic request/response schemas
  services/        feature-based business service packages
  tests/           backend tests
  utils/
    config/        app settings
    errors/        app exceptions and DB error helpers
    transactions/  transaction upload parsing and validation helpers
    secrets/       local environment files
frontend/
  src/             React UI skeleton
docker-compose.yml
requirements.txt
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop or Docker Engine, only if using PostgreSQL instead of SQLite

## 1. Backend Environment

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create the local backend environment file:

```bash
cp backend/utils/secrets/.env.example backend/utils/secrets/.env
```

Default PostgreSQL database URL:

```text
postgresql+psycopg://postgres:postgres@localhost:5432/lumina_finance
```

SQLite fallback URL, if you want to run without Docker:

```text
sqlite:///./lumina_finance.db
```

## 2. Choose And Initialize The Database

### Option A: PostgreSQL With Docker Compose

```bash
docker compose up -d postgres
```

Check that the container is running:

```bash
docker compose ps
```

### Option B: SQLite Without Docker

Change `DATABASE_URL` in `backend/utils/secrets/.env` to:

```text
sqlite:///./lumina_finance.db
```

This creates a local `lumina_finance.db` file in the project root when tables are initialized.

### Initialize Tables

The backend initializes tables automatically on startup by default. Set `AUTO_INIT_DB=false` in `backend/utils/secrets/.env` if you want to disable that.

Startup creates:

- `transactions`
- `positions`
- `violations`

## 3. Run Backend API

```bash
uvicorn backend.main:app --reload
```

Backend URLs:

- API root: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

Registered endpoints:

- `POST /upload-transactions`
- `GET /clients`
- `GET /clients/{client_id}/positions`
- `GET /violations`
- `GET /analytics`

## 4. Run Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://127.0.0.1:5173
```

## 5. Sample Data

The sample workbook is stored at:

```text
backend/utils/samples/transactions_sample.xlsx
```

Uploads support `.xlsx` and `.csv` files with these transaction columns:

- `ClientId`
- `TransactionId`
- `ISIN`
- `Action`
- `Quantity`
- `Price`
- `Timestamp`

## 6. Tests And Verification

Run backend tests:

```bash
source .venv/bin/activate
python -m pytest backend/tests
```

Run backend syntax check:

```bash
python -m compileall backend
```

Build frontend:

```bash
cd frontend
npm run build
```

## 7. Stop Services

Stop PostgreSQL while keeping the database volume:

```bash
docker compose down
```

Stop PostgreSQL and delete local database data:

```bash
docker compose down -v
```

## Notes

- `backend/utils/secrets/.env` is ignored by git and should contain local secrets only.
- `backend/utils/secrets/.env.example` is the shareable template.
- PostgreSQL is the recommended setup for this project, and SQLite can be used by changing only `DATABASE_URL`.
- `POST /upload-transactions` parses CSV/XLSX files, normalizes and validates transactions, applies FIFO in chronological order, persists transactions, stores refreshed current positions, and returns only an upload summary.
- `GET /clients` lists distinct client IDs from transaction data.
- `GET /clients/{client_id}/positions` reads stored positions per ISIN with realized and unrealized P&L.
- `GET /violations` reads persisted compliance violations.
- `GET /analytics` returns top traded ISINs, client holding-time averages, the most volatile client, and ISIN concentration reports.
- Database tables are created directly from SQLAlchemy metadata.
