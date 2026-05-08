# Lumina Finance Platform

A skeleton finance platform with a FastAPI backend, PostgreSQL database, SQLAlchemy models, Swagger UI, and a simple React frontend.

The API and service business logic is intentionally left as TODOs. The database infrastructure and project setup are runnable.

## Tech Stack

- Backend: Python, FastAPI, SQLAlchemy, pandas
- Database: PostgreSQL
- Frontend: React with Vite
- API docs: Swagger UI through FastAPI

## Project Structure

```text
backend/
  controller/      API controller layer
  db/              database engine, sessions, initialization helpers
  models/          SQLAlchemy models
  routes/          FastAPI route declarations
  samples/         sample input files
  schemas/         Pydantic request/response schemas
  secrets/         local environment files
  services/        business service layer
  tests/           backend tests
  utils/           shared utilities and settings
frontend/
  src/             React UI skeleton
docker-compose.yml
requirements.txt
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop or Docker Engine

## 1. Backend Environment

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create the local backend environment file:

```bash
cp backend/secrets/.env.example backend/secrets/.env
```

Default database URL:

```text
postgresql+psycopg://postgres:postgres@localhost:5432/lumina_finance
```

## 2. Start PostgreSQL

```bash
docker compose up -d postgres
```

Check that the container is running:

```bash
docker compose ps
```

Initialize the database tables:

```bash
python -m backend.db.init_db
```

This creates:

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
backend/samples/transactions_sample.xlsx
```

It contains these transaction columns:

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

- `backend/secrets/.env` is ignored by git and should contain local secrets only.
- `backend/secrets/.env.example` is the shareable template.
- API/service methods currently return TODO responses or raise TODO implementation placeholders.
- Database tables are created directly from SQLAlchemy metadata.
