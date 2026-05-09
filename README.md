# Lumina Finance Platform

Mini full-stack financial transactions platform for Lumina Capital. The app
uploads transaction files, validates them, stores processed data, calculates
FIFO positions and P&L, detects rule violations, exposes analytics, and shows
the results in a React UI.

## Stack

- Backend: Python, FastAPI, SQLAlchemy, pandas
- Database: SQLite by default; PostgreSQL is also supported through `DATABASE_URL`
- Frontend: React with Vite
- Tests: pytest

## Structure

```text
backend/
  app/
    main.py              FastAPI app factory
    config.py            settings and logging
    exceptions.py        API/domain exceptions
    api/routes/         upload, clients, positions, violations, analytics
    db/base.py           SQLAlchemy declarative base
    db/session.py        engine, sessions, schema initialization
    models/              transaction, position, violation ORM models
    repositories/        database access layer
    schemas/             Pydantic request/response models by domain
    services/
      shared/
        csv_handler.py       CSV/XLSX parsing
        dataframe_utils.py   reusable dataframe cell normalization
        decimal_utils.py     shared Decimal constants and formatting
        math_utils.py        shared finance math
      transactions/
        transactions_service.py transaction upload orchestration
        schemas.py           transaction processing DTOs
        helpers/             upload parsing, validation, and responses
      clients/
        query_service.py     client listing use case
      positions/
        positions_service.py client position response assembly
        schemas.py           position service DTOs and protocols
        helpers/             position snapshot helpers
      analytics/
        analytics_service.py analytics orchestration
        schemas.py           analytics service DTOs and protocols
        helpers/             analytics calculations
      violations/
        violations_service.py violation orchestration, queries, validation
        schemas.py           violation rule abstractions and DTOs
        helpers/             individual violation detectors
  tests/
    helpers/             API fixtures and mock row factories
    test_api.py
    test_logic.py
  requirements.txt
data/
  transactions_sample.xlsx
frontend/
  src/
    App.jsx
    services/api.js
AI_USAGE.md
docker-compose.yml
requirements.txt
```

## Backend Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp backend/.env.example backend/.env
```

The default `backend/.env.example` uses PostgreSQL:

```text
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/lumina_finance
```

For SQLite without Docker, change it to:

```text
DATABASE_URL=sqlite:///./backend/lumina.db
```

If no `.env` file exists, the backend also falls back to SQLite at
`backend/lumina.db`.

## Run Backend

SQLite:

```bash
uvicorn backend.app.main:app --reload
```

PostgreSQL:

```bash
docker compose up -d postgres
uvicorn backend.app.main:app --reload
```

API docs: `http://127.0.0.1:8000/docs`

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

Validation rules:

- `Quantity > 0`
- `Price > 0`
- `Action` is `Buy` or `Sell`

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

The UI uploads CSV/XLSX files, lists clients, displays positions, displays
violations, and shows analytics from the backend API.

## Tests

```bash
python -m pytest backend/tests
python -m compileall backend
```

Frontend build check:

```bash
cd frontend
npm run build
```
