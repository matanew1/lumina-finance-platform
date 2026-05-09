# Lumina Finance Platform

Mini full-stack financial transactions platform for Lumina Capital. The app
uploads transaction files, validates them, stores processed data, calculates
FIFO positions and P&L, detects rule violations, exposes analytics, and shows
the results in a React UI.

## Stack

- Backend: Python, FastAPI, SQLAlchemy, pandas
- Database: PostgreSQL with Docker Compose, or SQLite for simple local runs
- Frontend: React with Vite
- Tests: pytest

## Project Structure

```text
backend/
  app/
    main.py                  FastAPI app factory
    api/routes/              upload, clients, positions, violations, analytics
    api/schemas/             API response models by domain
    db/                      SQLAlchemy base, engine, sessions, schema init
    models/                  transaction, position, violation ORM models
    repositories/            database access layer
    services/
      shared/                CSV parsing, dataframe utilities, Decimal helpers, FIFO math
      transactions/          upload orchestration, DTOs, ingestion helpers
      clients/               client listing use case
      positions/             client position responses and position snapshots
      analytics/             analytics orchestration and calculations
      violations/            violation orchestration and detector rules
    utils/                   config, logging, app exceptions
  tests/
    helpers/                 API fixtures and mock row factories
    test_api.py
    test_logic.py
  Dockerfile
  requirements.txt
data/
  transactions_sample.xlsx
frontend/
  src/
    App.jsx
    services/api.js
  Dockerfile
docker-compose.yml
requirements.txt
```

## Flow 1: Docker Compose

Use this path when you want the full app with one command. It starts:

- PostgreSQL on `localhost:5432`
- FastAPI on `http://localhost:8000`
- React/Vite on `http://localhost:5173`

```bash
docker compose up --build
```

Then open:

- Frontend: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`

The backend container uses PostgreSQL through the internal Compose hostname
`postgres`:

```text
postgresql+psycopg://postgres:postgres@postgres:5432/lumina_finance
```

Stop the app:

```bash
docker compose down
```

Stop the app and delete the PostgreSQL volume:

```bash
docker compose down -v
```

## Flow 2: Manual Local Setup

Use this path when you want to run backend and frontend directly on your
machine.

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp backend/.env.example backend/.env
```

For SQLite without Docker, set this in `backend/.env`:

```text
DATABASE_URL=sqlite:///./backend/lumina.db
```

Backend settings are loaded from environment variables or `backend/.env`.
All keys shown in `backend/.env.example` are required; the app does not rely on
hardcoded runtime defaults for database URL, CORS, logging, or app settings.

For PostgreSQL, keep the default `backend/.env.example` database URL and start
Postgres:

```bash
docker compose up -d postgres
```

Run the backend:

```bash
uvicorn backend.app.main:app --reload
```

API docs: `http://localhost:8000/docs`

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

The frontend defaults to `http://localhost:8000` for the backend API. Override it
with `VITE_API_BASE_URL` if needed.

## API

- `POST /upload-transactions`
- `GET /clients`
- `GET /clients/{client_id}/positions`
- `GET /violations`
- `GET /analytics`

## Input File

Sample workbook:

```text
data/transactions_sample.xlsx
```

Required columns:

- `ClientId`
- `TransactionId`
- `ISIN`
- `Action`
- `Quantity`
- `Price`
- `Timestamp`

Rules:

- `Quantity > 0`
- `Price > 0`
- `Action` is `Buy` or `Sell`

## Tests

Backend:

```bash
python -m pytest backend/tests
python -m compileall backend
```

Frontend:

```bash
cd frontend
npm run build
```
