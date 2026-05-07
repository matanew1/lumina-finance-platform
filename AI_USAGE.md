# AI Usage

## AI Tools Used
- Codex 5.5 as Developer Agent
- Claude Code Sonnet 4.6 as Reviewer Agent

---

## Phase 1 - Project Skeleton

### Example Prompts
- Create a clean FastAPI, SQLAlchemy, PostgreSQL backend skeleton with route/controller/service/model/db layers.
- Add TODO-only endpoint stubs for upload transactions, clients, positions, violations, and analytics.
- Review `backend/samples/transactions_sample.xlsx` only for schema clues, without implementing business logic.
- Add a simple React UI skeleton without implementing functional behavior.

### Generated Code
- Created the initial FastAPI backend skeleton with routes, controllers, services, models, database setup, schemas, utils, and tests.
- Created SQLAlchemy model skeletons for `transactions`, `positions`, and `violations`.
- Created Pydantic API schemas for clients, transactions, positions, violations, and analytics.
- Created a simple React/Vite frontend skeleton.
- Added route-registration tests for the required API endpoints.

### Verification
- Ran Python compile checks for the backend.
- Installed frontend dependencies and verified the React/Vite app builds.
- Installed backend dependencies in a local `.venv` and verified the initial backend tests.

### Mistakes And Fixes
- No mistakes found !
---

## Phase 2 - Improve Layer Separation

### Example Prompts
- Separate shared route, controller, and service files.

### Generated Code
- Split the original shared route/controller/service files into separate feature-based modules:
  - transaction routes/controller/service
  - client routes/controller/service
  - position routes/controller/service
  - violation routes/controller/service
  - analytics routes/controller/service
- Kept `backend/routes/api_routes.py` as a router aggregator only.

### Modified Code
- Removed `main_controller.py` and `main_service.py` after splitting them.

### Verification
- Confirmed no stale `MainController` or `MainService` references remained.
- Ran backend compile checks.
- Ran backend tests successfully.

---

## Phase 3 - Database Infrastructure

### Example Prompts
- Add Docker Compose PostgreSQL and connect to the database.
- Fully implement the database infrastructure only.

### Generated Code
- Added `docker-compose.yml` using `postgres:16-alpine`.
- Added a persistent PostgreSQL volume and healthcheck.
- Added SQLAlchemy database connection infrastructure.
- Added database initialization helpers for creating, dropping, and listing tables.
- Added database metadata tests for required tables and transaction columns.
- Added database constraints/defaults to transaction, position, and violation models.

### Modified Code
- Updated `backend/db/session.py` with engine/session setup and a database connectivity check.
- Updated `backend/models/base.py` with SQLAlchemy naming conventions.
- Updated `backend/db/init_db.py` with `init_db()`, `drop_db()`, and `get_table_names()`.
- Updated SQLAlchemy models to include constraints and server defaults.

### Verification
- Ran `python3 -m compileall backend`.
- Ran `.venv/bin/python -m pytest backend/tests`.
- Started the PostgreSQL Docker container with `docker compose up -d postgres`.

### Mistakes And Fixes
- No mistakes found !
---

## Current Notes
- API and service business logic is still intentionally TODO-only.
- Database infrastructure is implemented, but live table initialization should be run locally with the PostgreSQL container available.
- Runtime environment variables live in `backend/secrets/.env`; the shareable example lives in `backend/secrets/.env.example`.
- The sample workbook lives at `backend/samples/transactions_sample.xlsx`.
