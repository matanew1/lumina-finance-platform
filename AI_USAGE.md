# AI Usage

## AI Tools Used

- **Codex**
  - Generated the initial project plan and skeleton
  - Helped scaffold backend, frontend, tests, and Docker setup
  - Assisted with refactors and debugging

- **Claude Code**
  - Reviewed the financial logic, FIFO calculations, edge cases, and performance issues

---

## How I Worked With AI

1. Read the assignment to fully understand the requirements and financial rules.

2. Asked Codex to generate:
   - a high-level implementation plan
   - an initial project skeleton with `TODO / not implemented` placeholders

3. Reviewed and modified the generated structure to match the architecture I wanted.

4. Built the system incrementally from simpler flows to more complex financial logic, starting with one thin slice:

   `upload → service → repository → DB → response → UI`

5. Manually reviewed all generated code:
   - ran tests
   - reorganized files
   - simplified logic
   - optimized performance-critical paths

6. Used Claude Code as a second-pass reviewer for financial correctness, edge cases, and performance issues.

---

## Example Prompts

- Build a FastAPI + SQLAlchemy backend with routes, services, repositories, and tests for a transaction upload flow.
- Create an initial project skeleton with `TODO / not implemented` placeholders.
- Add FIFO position math with realized and unrealized P&L.
- Add violation rules such as sell-before-buy, day trading, and risk concentration.
- Add analytics endpoints and calculations.
- Build a React + Vite UI for uploads, positions, violations, and analytics.
- Review the FIFO implementation and identify precision or performance issues.

---

## What Code Was Generated

AI generated the initial scaffolding and first-pass implementations for:

- FastAPI backend structure
- routes, services, repositories, and schemas
- SQLAlchemy models
- upload pipeline
- FIFO logic
- violation rules
- analytics calculations
- React dashboard
- tests
- Docker Compose setup

I later reviewed, reorganized, optimized, and corrected the implementation manually.

---

## What I Modified

### Architecture

- Reorganized the backend into layered folders under `backend/app`
- Split services by domain:
  - transactions
  - clients
  - positions
  - violations
  - analytics
- Moved DB access into repositories
- Simplified unnecessary abstractions
- Replaced the `ViolationRule` abstract class with simple callable functions

### Performance

- Moved FIFO recomputation from read-time into the upload pipeline
- Replaced list front-removal with `collections.deque` and `popleft()` to avoid O(n²) behavior
- Added running totals to make position reads O(1)

### Financial Correctness

I manually reviewed and improved the financial algorithms instead of relying on the initial generated logic.

Key improvements included:

- Rewriting realized and unrealized P&L calculations for better correctness and readability
- Fixing 24-hour trading window edge case where trades exactly 24h old were incorrectly included in the active window
- Simplifying parts of the FIFO implementation for better correctness and readability
- Optimizing position calculations to avoid repeated traversal of open lots

### Reliability

- Fixed valid CSV uploads incorrectly returning `400`
- Added proper `201 / 400 / 409` status handling
- Fixed incorrect client retrieval logic
- Resolved circular import issues during schema cleanup

---

## Mistakes And How I Fixed Them

- FIFO positions were recomputed on every read request.
  - I moved recomputation into the upload pipeline and persisted the results.

- FIFO processing used inefficient list front-removal.
  - I replaced it with `collections.deque` and `popleft()`.

- 24-hour trading window incorrectly included trades exactly 24 hours old.
  - I fixed the boundary condition logic so the window behaves correctly at the exact cutoff time.

- `GET /clients` incorrectly depended on positions data.
  - I changed it to read from transactions instead.

- Schema cleanup introduced circular imports.
  - I reorganized imports and shared schemas.