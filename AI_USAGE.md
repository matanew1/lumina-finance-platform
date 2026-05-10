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

- Reorganized backend into layered structure (`routes / services / repositories / schemas`)
- Split services by domain (transactions, clients, positions, violations, analytics)
- Moved DB access into repositories
- Simplified unnecessary abstractions
- Replaced rule abstraction with simple callable functions

### Performance

- Moved FIFO computation from read-time into upload pipeline
- Replaced list queue operations with `collections.deque` to avoid O(n²)
- Added running totals to make position reads O(1)

### Financial Correctness

- Rewriting realized and unrealized P&L calculations for correctness
- Fixing 24-hour trading window edge case where boundary trades (exactly at `now - 24h`) were incorrectly included; fixed by using a strict cutoff (`timestamp > now - 24h`)
- Simplifying FIFO logic for readability and correctness
- Reducing repeated traversal of open lots in position calculations

---

## Mistakes And How I Fixed Them

- FIFO positions were recomputed on every read request  
  → Moved recomputation into the upload pipeline and persisted results

- FIFO processing used inefficient list front-removal (O(n²) behavior)  
  → Replaced with `collections.deque` and `popleft()` (O(1))

- 24-hour trading window incorrectly included boundary-edge trades  
  → Fixed by enforcing strict cutoff logic (`timestamp > now - 24h` instead of `>=`)

- `GET /clients` incorrectly depended on positions data  
  → Changed to read directly from transactions

- Circular imports introduced during schema refactor  
  → Restructured shared schema imports and fixed module dependencies