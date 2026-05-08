# AI Usage

## AI Tools Used

- Codex 5.5 as Developer Agent
- Claude Code Sonnet 4.6 as Reviewer Agent

---

## Section 1 - Setup And Infrastructure

### Phase 1 - Project Skeleton

#### Example Prompts

- Create a clean FastAPI, SQLAlchemy, PostgreSQL backend skeleton with route/controller/service/model/db layers.
- Add TODO-only endpoint stubs for upload transactions, clients, positions, violations, and analytics.
- Review `backend/utils/samples/transactions_sample.xlsx` only for schema clues, without implementing business logic.
- Add a simple React UI skeleton without implementing functional behavior.

#### Generated Code

- Created the initial FastAPI backend skeleton with routes, controllers, services, models, database setup, schemas, utils, and tests.
- Created SQLAlchemy model skeletons for `transactions`, `positions`, and `violations`.
- Created Pydantic API schemas for clients, transactions, positions, violations, and analytics.
- Created a simple React/Vite frontend skeleton.
- Added route-registration tests for the required API endpoints.

#### Verification

- Ran Python compile checks for the backend.
- Installed frontend dependencies and verified the React/Vite app builds.
- Installed backend dependencies in a local `.venv` and verified the initial backend tests.

#### Mistakes And Fixes

- None recorded for this phase.

---

### Phase 2 - Layer Separation

#### Example Prompts

- Separate shared route, controller, and service files.

#### Generated Code

- Split the original shared route/controller/service files into separate feature-based modules.
- Added separate transaction route/controller/service files.
- Added separate client route/controller/service files.
- Added separate position route/controller/service files.
- Added separate violation route/controller/service files.
- Added separate analytics route/controller/service files.
- Consolidated route declarations and controller classes into `backend/controllers`.
- Kept `backend/controllers/api_controller.py` as a router aggregator only.

#### Modified Code

- Removed `main_controller.py` and `main_service.py` after splitting them.

#### Verification

- Confirmed no stale `MainController` or `MainService` references remained.
- Ran backend compile checks.
- Ran backend tests successfully.

#### Mistakes And Fixes

- None recorded for this phase.

---

### Phase 3 - Database Infrastructure

#### Example Prompts

- Add Docker Compose PostgreSQL and connect to the database.
- Fully implement the database infrastructure only.

#### Generated Code

- Added `docker-compose.yml` using `postgres:16-alpine`.
- Added a persistent PostgreSQL volume and healthcheck.
- Added SQLAlchemy database connection infrastructure.
- Added database initialization helpers for creating, dropping, and listing tables.
- Added database metadata tests for required tables and transaction columns.
- Added database constraints/defaults to transaction, position, and violation models.

#### Modified Code

- Updated `backend/db/session.py` with engine/session setup and a database connectivity check.
- Updated `backend/db/models/base.py` with SQLAlchemy naming conventions.
- Updated `backend/db/init_db.py` with `init_db()`, `drop_db()`, and `get_table_names()`.
- Updated SQLAlchemy models to include constraints and server defaults.

#### Verification

- Ran `python3 -m compileall backend`.
- Ran `.venv/bin/python -m pytest backend/tests`.
- Started the PostgreSQL Docker container with `docker compose up -d postgres`.

#### Mistakes And Fixes

- None recorded for this phase.

---

### Phase 4 - Documentation

#### Example Prompts

- Write README instructions for full project setup.
- Organize the AI usage file by phases.

#### Generated Code

- Created `README.md` with setup instructions for backend, database, frontend, tests, and sample data.
- Organized `AI_USAGE.md` into sections and phases.

#### Modified Code

- Updated environment path references to `backend/utils/secrets/.env` and `backend/utils/secrets/.env.example`.
- Updated sample workbook references to `backend/utils/samples/transactions_sample.xlsx`.

#### Verification

- Verified referenced secret and sample paths exist.
- Reviewed README setup commands against the current project structure.

#### Mistakes And Fixes

- Corrected the typo `Infracrtusture` to `Infrastructure`.

---

## Section 2 - Business Logic

### Phase 1 - Data Ingestion And Validation

#### Example Prompts

- Implement Part A: load and parse the Excel file, normalize data, and validate quantity, price, and action.

#### Generated Code

- Implemented `POST /upload-transactions` business logic.
- Added Excel parsing with pandas and `openpyxl`.
- Added column normalization from workbook headers such as `ClientId`, `TransactionId`, `ISIN`, `Action`, `Quantity`, `Price`, and `Timestamp`.
- Added value normalization for strings and action casing.
- Added validation errors for invalid rows.
- Added transaction upload response schemas.
- Added repository files for transaction database writes.
- Added generic exceptions for conflict and persistence failures.
- Added generic reusable utilities for upload parsing, DataFrame cleanup, and database error detection.
- Added ingestion tests for successful uploads, validation failures, duplicate conflicts, and invalid file types.
- Refactored ingestion tests to use pytest fixtures and async pytest markers instead of manual `asyncio.run`.

#### Modified Code

- Updated `backend/services/transactions/transaction_service.py` to parse, normalize, validate, and persist valid uploaded transactions.
- Updated `backend/controllers/transaction_controller.py` to return HTTP errors for invalid upload files and persistence failures.
- Updated `backend/controllers/transaction_controller.py` with a real upload response model.
- Updated `backend/schemas/transaction_schema.py` with strict action, quantity, and price validation.
- Updated `backend/db/models/transaction.py` so the database also enforces `price > 0`.
- Moved generic helper functions into `backend/utils/upload_utils.py`, `backend/utils/dataframe_utils.py`, and `backend/utils/db_errors.py`.
- Moved transaction-specific ingestion helper functions into `backend/services/transactions/transaction_ingestion.py`.
- Moved transaction database persistence into `backend/db/repositories/transaction_repository.py`.
- Updated duplicate transaction handling to return HTTP `409 Conflict`.

#### Validation Rules

- `Quantity > 0`
- `Price > 0`
- `Action` must be `Buy` or `Sell`

#### Verification

- Ran `python3 -m compileall backend`.
- Ran `.venv/bin/python -m pytest backend/tests`.
- Confirmed `8` backend tests pass.

#### Mistakes And Fixes

- Found the database model allowed `price >= 0`, while the required validation says `price > 0`.
- Fixed the SQLAlchemy check constraint to enforce `price > 0`.

---

## Current Project Notes

- Runtime environment variables live in `backend/utils/secrets/.env`.
- The shareable environment template lives in `backend/utils/secrets/.env.example`.
- The sample workbook lives at `backend/utils/samples/transactions_sample.xlsx`.
- Database infrastructure is implemented.
- Live table initialization should be run locally with the PostgreSQL container available.
