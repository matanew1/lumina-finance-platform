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
- Ran `.venv/bin/python -m pytest backend/tests/test_transaction_ingestion.py`.
- Confirmed `5` backend tests pass.

#### Mistakes And Fixes

- Found the database model allowed `price >= 0`, while the required validation says `price > 0`.
- Fixed the SQLAlchemy check constraint to enforce `price > 0`.

---

### Phase 2 - FIFO Positions And P&L

#### Example Prompts

- Implement FIFO cost calculation, realized and unrealized P&L, and positions per ISIN.
- Keep the work modular with subfolders.

#### Generated Code

- Added `backend/services/positions` as a modular subfolder for position business logic.
- Added FIFO purchase-batch consumption and position calculation helpers.
- Added client position service logic for `GET /clients/{client_id}/positions`.
- Added ordered transaction reads for upload-time position rebuilding.
- Added Pydantic response schemas for computed positions and totals.
- Added tests for FIFO calculations, service totals, and endpoint responses.
- Split position read queries into a dedicated repository to keep transaction persistence separate from position data access.
- Implemented `GET /clients` with a dedicated client repository and response model.
- Updated transaction upload to accept CSV or XLSX files.
- Updated transaction upload to recalculate and persist current positions after chronological FIFO processing.
- Updated `GET /clients/{client_id}/positions` to read persisted position rows instead of recalculating FIFO on each request.
- Updated `POST /upload-transactions` to return only the upload summary and validation errors, without echoing transaction rows.

#### Modified Code

- Kept `backend/controllers/client_controller.py` focused on client listing.
- Kept `backend/controllers/position_controller.py` focused on client position responses.
- Updated `backend/schemas/position_schema.py` with realized P&L, unrealized P&L, market value, cost basis, and totals.
- Moved position service logic into `backend/services/positions/position_service.py`.
- Added FIFO calculation logic in `backend/services/positions/fifo_calculator.py`.
- Added `backend/db/repositories/position_repository.py` for persisted position reads and writes.
- Added `backend/db/repositories/client_repository.py` for distinct client lookups from transactions.
- Updated `backend/services/transactions/transaction_service.py` to persist uploaded transactions and refreshed positions in one commit.
- Updated `backend/schemas/transaction_schema.py` so upload responses omit transaction row payloads.
- Updated `backend/utils/upload_utils.py` and transaction ingestion helpers for CSV/XLSX parsing.
- Updated `backend/services/positions/position_service.py` to act as a read service over persisted positions.
- Added computed position fields to `backend/db/models/position.py` so upload-time FIFO results can be stored.

#### Business Rules

- Buys create FIFO purchase batches.
- Sells consume the oldest available purchase batches first.
- Upload processing sorts transactions chronologically before applying FIFO.
- Position reads use the precomputed `positions` table and do not rerun FIFO.
- Upload responses include status, row counts, persisted row count, and validation errors only.
- Realized P&L is calculated when purchase batches are sold.
- Open positions are grouped per ISIN.
- Unrealized P&L uses the latest transaction price for that client and ISIN as the mark price.

#### Verification

- Ran `python3 -m compileall backend`.
- Ran `.venv/bin/python -m pytest backend/tests`.
- Confirmed `17` backend tests pass.

#### Mistakes And Fixes

- The initial `GET /clients` repository queried both `transactions` and `positions`.
- Fixed it to query only `transactions`, because transactions are the source of truth and positions are derived from FIFO processing.
- The position read service initially recalculated FIFO from transactions.
- Fixed it to read from the persisted `positions` table, because FIFO is now applied during transaction upload.

---

### Phase 3 - FIFO Optimization And Naming

#### Example Prompts

- Replace the FIFO list with a deque for O(1) front-pops and align names with financial-engineering conventions.

#### Generated Code

- Switched `PositionState.open_lots` from `list[OpenPurchaseBatch]` to `deque[OpenLot]` for O(1) `popleft()` instead of O(n) `list.pop(0)`.
- Renamed the lot abstraction to match cost-basis-accounting terminology:
  - `OpenPurchaseBatch` → `OpenLot`.
  - `open_purchase_batches` → `open_lots`.
  - `consume_oldest_purchase_batches` → `consume_oldest_lots`.

#### Modified Code

- Updated `backend/services/positions/fifo_calculator.py` to import `collections.deque` and use `popleft()` when a lot is fully consumed.
- Tightened the `positions` dict type hint to `dict[tuple[str, str], PositionState]` to match the `(client_id, isin)` key.
- Removed a stray `print(chronological_transactions)` debug statement from `calculate_fifo_positions`.

#### Verification

- Ran `.venv/bin/python -m pytest backend/tests/test_positions_business_logic.py`.
- Confirmed `4` positions tests pass after the refactor.

#### Mistakes And Fixes

- None recorded for this phase.

---

### Phase 4 - Position Schema Trim And FIFO Method Refactor

#### Example Prompts

- Switch `unrealized_pnl` to `quantity * (market_price - average_cost)` and remove anything that becomes redundant.
- Make the FIFO module simple and align it with Part C best practices.

#### Generated Code

- Replaced the `unrealized_pnl` formula in `PositionState` with `quantity * (market_price - average_cost)` (algebraically equivalent to the previous `market_value - cost_basis`).
- Inlined the cost-basis summation into `average_cost`, removing the `cost_basis` property.
- Removed `market_value` and `cost_basis` end-to-end: from `PositionState.as_dict`, `PositionRepository.update_client_positions`, `PositionService._position_to_response`, the `Position` SQLAlchemy model, and the `PositionRead` / `ClientPositionsResponse` schemas.
- Removed `total_market_value` from `ClientPositionsResponse` and from the totals computed in `PositionService.get_client_positions`.
- Folded the free `consume_oldest_lots` function into `PositionState.apply_sell`, and added a parallel `PositionState.apply_buy` so transaction handling lives with the data.
- Removed the redundant empty-positions early-return branch in `PositionService.get_client_positions` (the sum-with-`Decimal("0")`-seed already handles the empty-list case).
- Removed a debug `print()` from the FIFO sell loop and trimmed redundant inline comments that described what the code already says.

#### Modified Code

- Updated `backend/services/positions/fifo_calculator.py` with the new `unrealized_pnl` formula, inlined `average_cost`, and `apply_buy` / `apply_sell` methods on `PositionState`.
- Updated `backend/services/positions/position_service.py` to drop the empty-list branch and remove `cost_basis`, `market_value`, and `total_market_value` from the response shape.
- Updated `backend/db/repositories/position_repository.py` to stop writing `cost_basis` and `market_value`.
- Updated `backend/db/models/position.py` to drop the `cost_basis` and `market_value` columns.
- Updated `backend/schemas/position_schema.py` to drop `cost_basis`, `market_value`, and `total_market_value`.
- Updated `backend/tests/test_db_metadata.py` and `backend/tests/test_positions_business_logic.py` to remove the dropped fields from fixtures, helpers, kwargs, and assertions.

#### Verification

- Ran `.venv/bin/python -m pytest backend/tests`.
- Confirmed `17` backend tests pass.

#### Mistakes And Fixes

- A prior intermediate state commented out the `market_value` property while `as_dict()` still referenced it, which would have raised `AttributeError` on every upload.
- Resolved by removing both the property and the `as_dict()` reference (and all downstream consumers) in the same change set.
- Note: dropping the `cost_basis` and `market_value` columns only takes effect against a fresh database, since initialization uses `create_all`. Existing local databases keep the now-unused columns until recreated.

---

## Current Project Notes

- Runtime environment variables live in `backend/utils/secrets/.env`.
- The shareable environment template lives in `backend/utils/secrets/.env.example`.
- The sample workbook lives at `backend/utils/samples/transactions_sample.xlsx`.
- Database infrastructure is implemented.
- Live table initialization should be run locally with the PostgreSQL container available.
