# AI Usage

## AI Tools Used

- **Codex**: implementation, refactoring, test cleanup, debugging, and documentation.
- **Claude Code Sonnet 4.6**: reviewer-style feedback on business logic and structure.

## Main Example Prompts

These prompts show the main development flow.

- Build a FastAPI finance backend with SQLAlchemy models, repositories, services, routes, and tests.
- Implement CSV/XLSX transaction upload with parsing, normalization, row validation, duplicate handling, and upload summary responses.
- Implement FIFO position calculation with realized P&L, unrealized P&L, and persisted client positions.
- Add violation detection for invalid values, sell-before-buy, day trading, and risk concentration.
- Add analytics for top traded ISINs, average holding time, most volatile client, and ISIN concentration.
- Split the original route file into feature route modules.
- Split rule logic by single responsibility.
- Restructure services into domain folders: transactions, clients, positions, violations, analytics, and shared.
- Move reusable transaction helper logic into a transaction helpers folder.
- Move cross-domain helper logic into a shared services folder.
- Split API schemas by domain.
- Make `test_api.py` thinner by moving mocks and helper functions into test helper modules.
- Review the code structure against SRP and clean up files with too many responsibilities.
- Update Docker Compose so the full app can start at once, and document both Docker and manual setup flows.
- Make backend settings come from environment variables or `backend/.env` instead of hidden runtime defaults.
- Deduplicate repeated `TransactionView` and `PositionView` Protocol definitions across service schema files by moving them into a shared protocols module.
- Consolidate analytics service result models and API response schemas into a single source of truth to eliminate duplicated class bodies.
- Replace the `ViolationRule` ABC and its `evaluate`/`__call__` indirection with a plain `Callable` type alias so rules are just functions.
- Improve the day-trading sliding-window algorithm by using two separate timestamp deques instead of a single full-object deque with manual integer counters.

## What Code Was Generated

- FastAPI application setup, route modules, exception handlers, and response schemas.
- SQLAlchemy models and repository classes for transactions, positions, violations, clients, and analytics queries.
- Transaction upload flow that reads CSV/XLSX files, validates rows, persists transactions, recalculates positions, detects violations, and commits the result.
- FIFO finance logic for open lots, realized P&L, unrealized P&L, average cost, and market value.
- Violation detector modules for invalid values, sell-before-buy, day trading, and risk concentration.
- Analytics calculations for top traded ISINs, average holding time, most volatile client, and ISIN concentration.
- Shared helpers for upload parsing, dataframe cell normalization, Decimal formatting, and reusable finance math.
- Backend tests for API behavior and business logic.
- A React operations console that uploads transaction files and displays clients, positions, violations, and analytics.
- Docker setup for running PostgreSQL, FastAPI, and the React frontend together with `docker compose up --build`.
- README and project-structure documentation updates.

## My Thinking And Process

- I first used AI to generate a working vertical slice: API endpoints, database models, services, repositories, and tests.
- After the first implementation worked, I reviewed the structure and asked AI to separate files by responsibility instead of keeping large service or route modules.
- I moved from a broad controller/service layout into a clearer `backend/app` structure with domain-based packages.
- I separated API schemas, service DTOs, repositories, route modules, and helper functions so each layer has a clearer purpose.
- I treated tests as feedback. When endpoint tests failed, I used the failures to fix API contracts, response shapes, and error handling.
- I kept domain-specific code inside its domain folder and moved only reusable logic into `services/shared`.
- I added Docker Compose only after the app structure was stable, so container setup reflected the real backend, frontend, and database boundaries.
- I made environment configuration explicit: Docker injects variables through Compose, while manual local setup uses `backend/.env`.
- I used the AI output as a draft, then refined naming, boundaries, and module ownership to make the project easier to review.

## What I Modified

- Reorganized backend code into a single `backend/app` application package.
- Replaced one large route module with feature route modules.
- Split API response schemas by domain.
- Moved database access into repositories.
- Split services into domain folders with `*_service.py`, `schemas.py`, and `helpers/` files.
- Moved dataframe parsing and Decimal percentage helpers into shared service utilities.
- Kept transaction upload response builders inside the transaction domain because they depend on transaction-specific response models.
- Moved test mocks, fake sessions, and helper functions out of `test_api.py`.
- Updated the frontend to use real backend endpoints instead of placeholder endpoint cards.
- Added Dockerfiles for backend and frontend and expanded Compose from database-only to full-stack startup.
- Updated backend config so required settings are injected from environment variables or `backend/.env`.
- Updated README and sample-data paths to match the final structure.
- Created `services/shared/protocols.py` as the single home for `TransactionView` and `PositionView` Protocols; deleted the three duplicate definitions that existed across the analytics, positions, and violations schema files.
- Merged analytics service result models with API response schemas by renaming the `*Result` variants to match the API names and adding `from_attributes=True`; made `api/schemas/analytics.py` a four-line re-export shim.
- Fixed the resulting circular import by updating `analytics_service.py` to import `AnalyticsResponse` from the service layer instead of the API layer, and removed the redundant `model_validate` round-trip.
- Replaced the `ViolationRule` ABC, `ViolationRule.evaluate`, and the `__call__` forwarding method with a `Callable` type alias; converted all four rule classes into plain `detect_*` functions.
- Rewrote the day-trading sliding window to use two separate timestamp-only deques (`buys`, `sells`) so `len()` replaces manual integer counters and the branched decrement pattern is removed.

## Mistakes And How I Fixed Them

- **Valid CSV uploads returned `400`.**  
  I fixed transaction parsing and error mapping so valid uploads return `201`, invalid files return `400`, and duplicate transaction IDs return `409`.

- **The upload response returned too much data.**  
  I changed it to return only upload status, row counts, persisted row count, and row-level errors.

- **`GET /clients` used the wrong source of truth.**  
  I changed it to read clients from uploaded transactions, because positions are derived data.

- **The position endpoint recalculated FIFO on read.**  
  I changed it to read persisted positions and kept FIFO recalculation in the upload workflow.

- **FIFO used the wrong data structure for oldest-lot removal.**  
  I replaced list front-removal with `collections.deque` and `popleft()`, improving repeated lot consumption from potential `O(n^2)` behavior toward `O(n)`.

- **FIFO state names were unclear.**  
  I clarified the model with names such as `OpenLot`, `PositionState`, and `PositionSchema`.

- **API tests became too heavy.**  
  I moved fake sessions, mock rows, and helper functions into `backend/tests/helpers`.

- **Some response schemas and test doubles drifted apart.**  
  I aligned test mocks with the real response models, including fields such as violation severity.

- **Risk concentration violations missed a useful transaction reference.**  
  I added position snapshots with the latest transaction ID for each client/ISIN and used that in violation drafts.

- **Analytics started as placeholder behavior.**  
  I replaced it with concrete analytics for traded ISINs, holding time, volatility, and concentration.

- **The first SRP pass still left too much logic in large files.**  
  I split transaction ingestion, violation detectors, analytics calculations, position snapshots, and shared helpers into smaller modules.

- **Documentation described an older structure.**  
  I rewrote the README and AI usage notes to match the final `backend/app` structure.

- **Docker Compose originally started only PostgreSQL.**  
  I updated it to start PostgreSQL, the FastAPI backend, and the React frontend together, with health checks and service dependencies.

- **The backend `.env` path was wrong after the app refactor.**  
  I fixed the config path so settings load from `backend/.env` instead of accidentally looking for `backend/app/.env`.

- **The backend could silently fall back to hardcoded config defaults.**  
  I made settings required so deployment and local setup must provide values through Compose environment variables or `backend/.env`.

- **Schema consolidation introduced a circular import.**  
  When `api/schemas/analytics.py` was made to import from `services/analytics/schemas.py`, and `analytics_service.py` still imported from `api/schemas/analytics.py`, Python hit a circular initialisation. I fixed it by moving the `AnalyticsResponse` import in `analytics_service.py` directly to the service-layer schema, which is the canonical owner.

- **The violations package `__init__.py` still exported the deleted Rule classes.**  
  After the four `*Rule` classes were removed, `violations/__init__.py` tried to import `DayTradingRule`, `InvalidValuesRule`, etc., causing an `ImportError` at startup. I removed those stale names and updated `__all__` to export only the `detect_*` functions.

