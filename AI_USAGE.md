# AI Usage

## AI Tools Used

- **Codex**
  - Used to generate the initial project plan and architecture skeleton
  - Helped scaffold backend, frontend, tests, and Docker setup
  - Assisted with refactors and debugging during implementation

- **Claude Code**
  - Used as a second-pass review tool for financial logic, FIFO correctness, edge cases, and performance issues

---

## How I Worked With AI

1. Read the assignment to fully understand the requirements, constraints, and financial rules.

2. Defined the architecture direction first, then used Codex to generate:
   - a high-level implementation plan
   - a project skeleton with `TODO / not implemented` placeholders

3. Aligned the generated structure with my intended architecture before writing core logic.

4. Built the system incrementally, starting with a single working slice:

   `upload → service → repository → DB → response → UI`

5. Implemented features step by step from simple flows to more complex financial logic.

6. Continuously validated and refined the system:
   - ran tests after each major change
   - simplified or refactored generated code when needed
   - optimized performance-critical paths

---

## Example Prompts

- Build a FastAPI + SQLAlchemy backend with layered architecture (routes, services, repositories, tests) for a transaction upload flow.
- Generate an initial project skeleton with placeholders (`TODO / not implemented`).
- Implement FIFO-based position tracking with realized and unrealized P&L.
- Add business rules for violations (sell-before-buy, day trading, risk concentration).
- Build analytics endpoints for portfolio insights.
- Create a React + Vite UI for uploading files and viewing results.
- Review FIFO logic for correctness, performance, and edge cases.

---

## What Code Was Generated

Codex generated the initial system structure and first-pass implementations for:

- FastAPI backend setup
- routes, services, repositories, and schemas
- SQLAlchemy models
- upload pipeline
- FIFO engine for position tracking
- violation detection rules
- analytics calculations
- React dashboard
- test suite
- Docker Compose environment

This code was treated as a starting point and later revised heavily.

---

## What I Modified

### Architecture Alignment

- Reorganized backend into clear layers under `backend/app`
- Split business logic into domains:
  - transactions
  - clients
  - positions
  - violations
  - analytics
- Ensured DB access is fully isolated in repositories
- Replaced abstract rule system with simple callable functions

### Performance Improvements

- Moved FIFO computation from read-time to write-time (upload pipeline)
- Replaced list-based FIFO queue with `collections.deque` to avoid O(n²) behavior
- Introduced running totals to make position reads O(1)

### Financial Logic Improvements

I reviewed and refined financial logic manually to ensure correctness and simplicity:

- Rewrote realized and unrealized P&L calculations for clarity and correctness
- Fixed 24-hour trading window edge case where trades exactly at the boundary were incorrectly included in the active window
- Simplified FIFO lot handling for better readability and correctness
- Reduced repeated traversal of open lots in position calculations

### Reliability Fixes

- Fixed valid CSV uploads incorrectly returning `400`
- Standardized API status handling (`201 / 400 / 409`)
- Corrected client retrieval logic
- Fixed circular import issues during schema refactor

---

## Mistakes And How I Fixed Them

- FIFO recomputation was happening on every read request
  - Fixed by persisting computed positions during upload

- FIFO implementation used list front-removal causing O(n²) performance
  - Fixed by replacing with `collections.deque`

- 24-hour trading window incorrectly included boundary-edge trades
  - Fixed by correcting time comparison logic to properly exclude exact boundary violations

- `GET /clients` depended incorrectly on derived position data
  - Fixed by sourcing directly from transactions

- Circular imports introduced during schema refactoring
  - Fixed by restructuring shared schema imports