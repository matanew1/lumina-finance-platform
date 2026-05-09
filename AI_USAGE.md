# AI Usage

## Tools

- **Codex** — wrote and refactored code.
- **Claude Code** — reviewed structure and ran a deep check on finance logic.
- **Antigravity IDE** — inline code suggestions while I typed.

## How I Worked With AI

- I built one thin slice first (upload → service → repo → DB → response → UI). This way I caught wiring bugs early.
- I treated every AI answer as a draft. I read the diff, ran the tests, then renamed and moved code before asking for the next change.
- I let failing tests guide my fixes. I did not refactor on a guess.
- I ran a second review pass only on places where bugs hide silently: FIFO math, the 24-hour window, and `Decimal` precision. I asked for a graded audit, not a generic review.
- I only fixed audit notes I could prove with a number example. I skipped the rest.

## Example Prompts

- Build a FastAPI + SQLAlchemy backend with routes, services, repositories, and tests for a transaction upload flow.
- Add FIFO position math with realized and unrealized P&L, saved per ISIN.
- Add violation rules: invalid values, sell before buy, day trading (more than 3 buy/sell pairs in 24h), and risk concentration (one ISIN over 50% of the portfolio).
- Add analytics: top 3 traded ISINs, average holding time per client, most volatile client, and ISINs held by more than 70% of clients.
- Build a React + Vite UI that uploads the file and shows clients, positions, violations, and analytics.
- Act as a senior finance auditor and grade the FIFO math, the 24-hour window, and `Decimal` precision.

## What Was Generated

- FastAPI app, routers per feature, error handlers, and response schemas.
- SQLAlchemy models and repositories for transactions, positions, violations, and clients.
- Upload pipeline: parse CSV/XLSX → validate → save → recompute positions → run violation rules.
- FIFO engine, four violation rules, and four analytics calculations.
- Pytest suite for the API and the business logic.
- React UI with upload and four data sections.
- Docker Compose for Postgres, backend, and frontend.

## What I Modified

- Moved the backend into `backend/app` with clear folders: `routes / services / repositories / schemas / helpers`.
- Split services by domain (transactions, clients, positions, violations, analytics). All DB calls now live in repositories.
- Replaced the `ViolationRule` abstract class with a `Callable` type. Each rule is now a plain `detect_*` function.
- Rewrote the day-trading window to use two timestamp deques instead of one big deque with manual counters.
- Moved `TransactionView` and `PositionView` into `schemas/shared.py` and deleted three duplicates.
- Added running totals (`total_quantity`, `total_cost_basis`) to `PositionState`. Reads are O(1) and have no rounding drift.
- Rounded money fields at the API boundary with `MONEY_QUANTUM = Decimal("0.000001")` to match the DB `Numeric(18, 6)`.
- Made settings required from `backend/.env` or environment. No more silent fallbacks.

## Mistakes And How I Fixed Them

- **Valid CSV uploads returned 400.** I fixed parsing and error mapping. Now 201 on success, 400 on bad file, 409 on duplicate IDs.
- **Positions endpoint recomputed FIFO on every read.** I moved FIFO to the upload step. The endpoint now reads from the DB.
- **FIFO used a list with front removal (O(n²)).** I switched to `collections.deque` and `popleft()`.
- **`GET /clients` read from positions.** Clients with only invalid or fully-closed trades disappeared. I switched to reading from the transactions table.
- **24-hour window was off by one moment.** It used `<`, so trades exactly 24h old still paired. I changed both loops to `<=` for `(t-24h, t]`.
- **`unrealized_pnl` leaked rounding error.** It divided cost basis and multiplied it back. I rewrote it as `market_price * total_quantity - total_cost_basis`.
- **`PositionState` walked all lots on every read.** I added running totals updated on each buy and sell.
- **Schema cleanup caused a circular import.** I made `analytics_service.py` import the schema from the service layer directly.
- **Analytics were placeholders.** I replaced them with the four required calculations.

## Claude's Adversarial Review

I asked Claude Code to act as a senior finance auditor and grade the FIFO engine, the 24-hour window, `PositionState` mutability, short-sell guards, and `Decimal` precision. Findings I fixed:

- **FIFO precision drift (high).** `unrealized_pnl = quantity * (market_price - average_cost)` divided cost basis then multiplied it back. This leaked sub-cent error. → Rewrote as `market_price * total_quantity - total_cost_basis`.
- **Day-trading window off by one (medium).** Strict `<` kept trades exactly 24h old in the window. → Switched both loops to `<=` and added a comment for `(t-24h, t]`.
- **O(L) reads in `PositionState` (medium).** `quantity`, `average_cost`, and `unrealized_pnl` each walked `open_lots`. `as_result()` walked it three times. → Added running totals updated on each trade. Reads are O(1).
- **Money rounding at the boundary (medium).** `Decimal` values flowed to the API at full precision, then DB rounded to `Numeric(18,6)`. The API and DB disagreed. → Rounded at the response with `MONEY_QUANTUM = Decimal("0.000001")`.
- **List front removal (low).** `list.pop(0)` is O(n²) under heavy selling. → Switched to `collections.deque` + `popleft()`.

Findings I skipped on purpose:
- **Concurrency hardening on uploads.** Out of scope for a one-process demo with SQLite.
- **Exact regulator definition of a "buy/sell pair".** The brief is loose. I matched adjacent buy ↔ sell to follow the spec.

