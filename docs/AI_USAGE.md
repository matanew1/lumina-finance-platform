# AI_USAGE.md

## AI Tools Used

- **Codex 5.5** - used as the main development agent for backend code, tests, refactoring, and documentation.
- **Claude Code Sonnet 4.6** - used as a reviewer agent for business-logic review, code-structure review, and refactor suggestions.

---

## Example Prompts

Only the main prompts are listed here.

- Create a clean FastAPI, SQLAlchemy, PostgreSQL backend skeleton with route/controller/service/model/db layers.
- Add Docker Compose PostgreSQL and connect the backend to the database.
- Implement transaction ingestion and validation: load Excel/CSV, normalize data, validate `quantity > 0`, `price > 0`, and action is `Buy` or `Sell`.
- Implement FIFO cost calculation, realized/unrealized P&L, and positions per ISIN.
- Improve FIFO performance by replacing list front-removal with `deque`, reducing the algorithm from potential `O(n^2)` behavior to `O(n)`.
- Move database operations into repositories and keep services/controllers separated.
- Review the business logic and suggest refactor changes for cleaner separation of concerns.
- Persist positions after transaction upload, then make `GET /clients/{client_id}/positions` read from the positions table.
- Implement violations: invalid values, sell before buy, day trading, and risk concentration.
- Implement Part F analytics through `GET /analytics`.
- Refactor service modules into class-based helpers and move shared service data shapes into `types.py` files.
- Reintroduce dataclasses in service `types.py` files where they make the business logic shorter and clearer.

---

## What Code Was Generated

- FastAPI controllers for:
  - `POST /upload-transactions`
  - `GET /clients`
  - `GET /clients/{client_id}/positions`
  - `GET /violations`
  - `GET /analytics`
- SQLAlchemy models for:
  - `transactions`
  - `positions`
  - `violations`
- Repository layer for:
  - transactions
  - positions
  - clients
  - violations
  - analytics
- Transaction ingestion logic using pandas for CSV/XLSX parsing.
- FIFO calculation logic for positions, realized P&L, and unrealized P&L.
- Upload workflow that:
  - validates transactions
  - persists transactions
  - recalculates positions
  - generates violations
  - commits the processed data together
- Violation service and rule classes.
- Analytics service, analytics report class, and response schema.
- Pytest tests for transaction upload, transaction validation, FIFO, violations, and analytics behavior.
- README setup instructions.

---

## What I Modified

I treated the AI output as a starting point, then changed it to make the project cleaner, more correct, and easier to review.

- **Project organization:** moved environment files into `backend/utils/secrets` and the sample workbook into `backend/utils/samples` so local configuration and sample data are separated from application code.
- **Naming clarity:** renamed the original DB-schema wording to API `schemas`, because these files describe request/response data and not database tables.
- **Layer separation:** refactored the backend into controller, service, repository, schema, model, DB, utility, and test layers instead of keeping too much logic in shared files.
- **Feature packaging:** grouped controllers and services into feature folders such as `analytics`, `clients`, `positions`, `transactions`, and `violations` for a consistent project structure.
- **Reviewer feedback:** applied Sonnet review feedback to improve business-logic structure and split responsibilities between controllers, services, and repositories.
- **Repository responsibility:** moved persistence and query logic out of generic utility/helper functions and into repository classes, so services focus on business flow.
- **Endpoint ownership:** kept `client_controller.py` responsible for `GET /clients` and `position_controller.py` responsible for `GET /clients/{client_id}/positions`.
- **Upload API contract:** changed `POST /upload-transactions` to return `201 Created` and return only summary fields plus validation errors, instead of echoing full transaction rows.
- **Source of truth:** changed `GET /clients` to read client IDs only from `transactions`, because positions are derived from uploaded transaction data.
- **FIFO execution flow:** changed `PositionService` to read stored positions instead of recalculating FIFO on every request, because FIFO is already applied after transaction upload.
- **FIFO performance:** replaced list-based front removal with `collections.deque`, improving oldest-lot consumption from potential `O(n^2)` behavior to `O(n)`.
- **Violation responses:** added persisted violation lookup and structured response fields, including severity and related transaction IDs where available.
- **Analytics:** replaced the TODO analytics endpoint with structured Part F analytics based on processed transactions and positions.
- **Analytics modularity:** consolidated analytics calculations into an `AnalyticsReports` class, so each report has one method and `AnalyticsService` only orchestrates data loading and report assembly.
- **Database setup:** kept PostgreSQL as the main Docker Compose setup while adding SQLite support through the SQLAlchemy connection string for easier local grading.
- **Service typing:** added local `types.py` files for analytics, clients, positions, transactions, and violations so shared protocols, aliases, and dataclasses live beside the services that use them.
- **Class-based service helpers:** converted standalone FIFO and analytics helper functions into `FifoCalculator` and `AnalyticsReports` classes.
- **Dataclass cleanup:** restored dataclasses for compact service state and draft objects such as `TransactionIngestionResult`, `PositionState`, `HoldingLot`, `ClientContext`, `PositionSnapshot`, and `ViolationDraft`.

---

## Mistakes And How I Fixed Them

These are only the issues that were caught through manual review/user feedback during development.

- **The first structure separated routes and controllers in a way that was too fragmented.**  
  Fixed by consolidating route and controller behavior per feature controller.

- **Client and position endpoints were temporarily merged into one combined controller.**  
  Fixed by splitting them back into separate `client_controller.py` and `position_controller.py` files for better separation of concerns.

- **Some DB operations were placed in utility/helper functions instead of repositories.**  
  Fixed by moving persistence and query logic into repository classes.

- **Duplicate transaction IDs needed proper HTTP behavior.**  
  Fixed by translating duplicate transaction persistence errors into `409 Conflict`.

- **A mistake was found in the validation rules.**  
  Fixed after manual review by aligning the validation with the assignment requirements: `quantity > 0`, `price > 0`, and `action` must be `Buy` or `Sell`.

- **The upload endpoint returned too much data.**  
  Fixed by removing the transaction row payload from the response and returning only:
  - `status`
  - `total_rows`
  - `valid_rows`
  - `invalid_rows`
  - `persisted_rows`
  - `errors`

- **`GET /clients` originally queried both `transactions` and `positions`.**  
  Fixed by querying only `transactions`, because transactions are the source of truth and positions are derived data.

- **`PositionService` recalculated FIFO even though FIFO already runs after transaction upload.**  
  Fixed by making `PositionService` read persisted rows from the `positions` table.

- **The FIFO naming was unclear.**  
  Fixed by replacing unclear lot/helper naming with clearer names such as `OpenLot`, `apply_buy`, and `apply_sell`.

- **FIFO lot consumption needed better performance.**  
  Fixed after user feedback by replacing list front-removal with `collections.deque`, improving the FIFO algorithm from potential `O(n^2)` behavior to `O(n)`.

- **The first simplification pass overused plain dictionaries.**  
  Fixed after user feedback by bringing back dataclasses in service `types.py` files where attribute access made the code shorter and easier to follow.

- **Risk concentration violations returned `transaction_id: null`.**  
  Fixed by attaching the latest transaction ID for the affected client/ISIN.

- **The violation endpoint test data was missing `severity`.**  
  Fixed by updating the fake violation records to match the response schema.

- **`GET /analytics` was only a TODO endpoint.**  
  Fixed by implementing structured analytics for:
  - top 3 most traded ISINs
  - average holding time per client
  - most volatile client
  - ISIN concentration report

- **The documentation could look PostgreSQL-only even though the assignment allowed SQLite as a minimum.**  
  Fixed by documenting PostgreSQL with Docker Compose and adding a SQLite `DATABASE_URL` fallback that can run without Docker.

---

## Validation

Final validation commands:

```bash
.venv/bin/pytest backend/tests
```

Final result:

- Current backend test suite passed: `5 passed`.
- FIFO calculation results were also checked manually against the Excel sample to make sure the AI-generated logic did not invent or distort the expected calculations.
- SQLite fallback configuration was covered by tests for the SQLAlchemy engine settings.
