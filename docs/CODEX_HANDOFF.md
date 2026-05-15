# Codex Handoff

Updated: 2026-05-14

## Current Goal

Upgrade the current FastAPI + PostgreSQL + Redis + Docker Worker + static frontend FastOJ prototype into an AI-explainable interview training OJ platform. The target includes AI explanation/review/hints, hidden-test isolation, Redis Streams worker flow, WebSocket-first judge status, Docker sandbox hardening, Vite + React + TypeScript frontend, tests, Docker verification, and README updates.

## Completed So Far

- Phase 0 dependency audit completed and recorded in `docs/dependency-audit.md`.
- Vite + React + TypeScript frontend implemented with Tailwind, Monaco, TanStack Query, Zustand, Zod, xterm, Shiki, @xyflow/react, and Pretext adapter.
- Frontend information architecture simplified into a problem library, focused workbench, and training graph.
- Workbench now keeps code editor and AI Copilot as the primary focus; statement, public cases, official solution, judge terminal, and submission trail are in a tabbed detail dock.
- AI Copilot details are collapsed behind expandable sections by default to reduce cognitive load.
- Workbench was upgraded again into a focused three-column layout with collapsible statement and result sidebars.
- Workbench sidebars now have smoother transitions, narrower collapsed width, drag handles, min/max widths, and localStorage persistence.
- Login/register moved from header inputs into a dedicated auth page.
- Unauthenticated workbench run/submit now routes the user to the dedicated login page instead of silently staying on the workbench.
- Main workflow buttons now include clearer labels and hover titles.
- Added a single-button function/ACM mode toggle. It changes localized text and mode-colored status dots instead of rendering two competing buttons.
- Added frontend-side Chinese/English i18n for navigation, auth, problem display text, verdict labels, hover verdict explanations, tabs, mode labels, and AI Copilot/submission trail text.
- Added static visual step panels for supported problem types so basic explanations do not require AI calls.
- Seed data now appends missing problems by slug and includes interview-list tasks plus AI algorithm practice tasks for logistic regression sigmoid, KNN, KMeans, scaled dot-product attention, softmax cross entropy, and attention mask application.
- Removed prototype testcase compatibility. Per user direction, this is a new project and function-mode input targets the current JSON-line format only.
- Seed data now normalizes existing seeded problems by slug instead of deleting testcase rows, so incompatible local DB testcase inputs are rewritten to JSON-line format without breaking historical testcase-result foreign keys.
- Pretext is wrapped by `frontend/src/lib/textLayout.ts` and used by problem cards, graph nodes, and submission trail summaries.
- Backend AI module implemented with disabled and OpenAI-compatible providers, structured explain/review/hint responses, JSON fallback wrapping, and hidden-test filtering.
- Added `.env.example`; real `.env` and `.env.*` files are ignored by git. DeepSeek and local llama.cpp both use `AI_PROVIDER=openai_compatible` with different `AI_BASE_URL` and `AI_MODEL` values.
- AI endpoints added under `/api/v1/ai`.
- Redis Streams judge queue implemented with consumer groups, ack, retry, dead-letter helpers, pending reclaim, and status pub/sub.
- Worker now consumes Redis Stream messages and publishes judge status through Redis instead of importing API WebSocket internals.
- API relays Redis judge status events to WebSocket clients.
- Submission detail and WebSocket status access are owner/admin aware.
- Sandbox execution is Docker-first with unsafe local execution gated by `FASTOJ_ALLOW_UNSAFE_LOCAL_EXECUTION=true`.
- Docker sandbox is Docker-first with disabled networking, memory/memswap limits, pids limit, cap drop, no-new-privileges, non-root execution, output truncation, and clearer verdict mapping. Source/stdin injection now uses Docker API archive copy into an ephemeral container workspace; tmpfs was removed because Docker Desktop worker-in-container mode did not extract archives into tmpfs reliably.
- Judge runtime includes Python `numpy==2.2.6` and CPU `torch==2.7.1+cpu` for AI algorithm submissions.
- Real API public run and full submit now pass for both Two Sum function mode and Valid Parentheses ACM mode.
- Alembic baseline added.
- Added `backend/scripts/migrate_or_stamp.py` so existing prototype databases with tables but no `alembic_version` are stamped safely before startup.
- README rewritten with architecture, AI provider, llama.cpp, migrations, testing, sandbox, WebSocket, and known limits.
- Checkpoint commit already exists: `74f7c68 chore: checkpoint codex progress`.
- Docker Compose startup fix commit exists: `e00a30c fix: make docker compose startup robust`.
- Frontend simplification commit exists: `b36053b refactor: simplify frontend training workspace`.
- Docker Compose now builds and starts successfully after Dockerfile fixes.
- Latest WIP adds token-expiry alert before auth redirect, AI provider response normalization for hint/explain/review, fixed-viewport workbench scrolling, sample explanations, expanded seeded testcase counts, and the Softmax expected-output correction without exposing hidden testcase contents.
- Current WIP adds a controlled AI model selector (`default`, `deepseek`, `qwen-local`), backend named AI profiles, localized graph labels, structured sample cards, local discussion/settings views, removal of visible old-site wording, and backend/frontend acceptance-rate clamping so invalid historical counts cannot show rates above 100%.
- Admin Problem Authoring Agent MVP added: admin-only draft creation, run/step tracing, draft list/detail, approve, and reject endpoints; `ProblemDraft`, `AgentRun`, and `AgentStep` persistence; sandbox-backed validation; and explicit approval before formal `Problem`, `TestCase`, and official `Solution` rows are created.
- Admin Console now includes a minimal Problem Agent panel for topic/difficulty/tags/mode/model input, AgentRun step timeline, draft preview, validation report, approve, and reject. It explicitly states that generated content remains a draft until approval.
- The Qwen local profile expects an OpenAI-compatible local server such as `llama-server` on `http://host.docker.internal:8080/v1`. `llama-server` is not installed in the current PATH, so the local Qwen server has not been started.

## Not Completed Yet

- Full browser manual acceptance path has not been executed by Codex.
- WebSocket fallback behavior has not been verified in a real browser session.
- Real Redis dead-letter behavior is covered by unit-level tests but not manually exercised end to end.
- Frontend bundle size is large because Monaco and Shiki are loaded directly.
- Function mode wrappers now support Python, C++, Java, JavaScript, TypeScript, Go, and selected simpler C signatures. C still needs expanded matrix/string harnesses for some AI tasks.
- Approved Python function-mode Agent drafts now carry dynamic function metadata into the public problem API, workbench starter generation, and submission wrapper. Non-Python arbitrary function-mode harness metadata is still not implemented; those drafts fail validation instead of being published as runnable function tasks.
- Docker sandbox compiled-language execution now redirects `input.txt` into the final program instead of piping it into the compiler, and `/tmp/work` permissions are relaxed with `chmod` so `nobody` can create compiled binaries without adding Linux capabilities.
- Docker Compose rebuild passed after the latest worker/dependency edits. After Docker Desktop was restarted on 2026-05-14, API and worker reported healthy, HTTP health and frontend returned 200, and worker-in-container Docker SDK access returned `True`.
- Browser manual acceptance still needs to be run end to end.
- In-app browser automation tooling is not currently exposed in this session, so visual browser acceptance was not run by Codex after the latest UI polish.

## Current Modified File List

Modified and new files after the latest UI/mode/i18n/problem-set work include `AGENTS.md`, frontend `main.tsx`, `styles.css`, `lib/api.ts`, `lib/i18n.ts`, `lib/problemModes.ts`, backend AI/auth/admin/solution/function-mode code, seed data, tests, README files, and Codex docs.

## Executed Commands And Results

- `uv sync`: passed.
- `uv sync --extra dev`: passed.
- `uv run ruff check .`: passed.
- `uv run pytest`: passed, 60 tests passed with 3 datetime deprecation warnings.
- `cd frontend && npm run build`: passed, with Monaco/Shiki chunk-size warnings.
- `cd frontend && npm test`: passed, 5 tests passed; jsdom printed expected canvas `getContext` warnings.
- `docker compose config`: passed.
- `docker compose up --build -d`: initially failed on Dockerfile package/install issues, then passed after Dockerfile fixes.
- `docker compose ps`: postgres, redis, api, worker, and judge runtime are running.
- `Invoke-WebRequest -UseBasicParsing http://localhost:8000/api/v1/health`: passed with HTTP 200 and `{"status":"healthy","app":"FastOJ"}`.
- `docker compose logs --tail=120 api worker`: API starts successfully; worker starts successfully.
- `cd frontend && npm run build`: passed after frontend information architecture simplification.
- `cd frontend && npm test`: passed after frontend information architecture simplification.
- `uv run ruff check .`: passed after frontend information architecture simplification.
- `docker compose up --build -d`: passed after frontend information architecture simplification; new frontend bundle is served by the API image.
- `Invoke-WebRequest -UseBasicParsing http://localhost:8000`: passed with HTTP 200 and returned frontend HTML.
- `cd frontend && npm run build`: passed after function/ACM mode and layout work, with Monaco/Shiki chunk-size warnings.
- `cd frontend && npm test`: passed, 6 test files and 8 tests passed; jsdom printed expected canvas `getContext` warnings.
- `uv run ruff check .`: passed after ruff import fixes.
- `uv run pytest`: passed, 63 tests passed with 3 datetime deprecation warnings.
- `docker compose up --build -d`: failed after latest changes because Docker Desktop Linux engine was unavailable at `npipe:////./pipe/dockerDesktopLinuxEngine`.
- `cd frontend && npm run build`: passed after auth/resizable sidebar work, with Monaco/Shiki chunk-size warnings.
- `cd frontend && npm test`: passed after auth/resizable sidebar work, 6 test files and 8 tests passed; jsdom printed expected canvas `getContext` warnings.
- `docker compose up --build -d`: passed after auth/resizable sidebar work.
- `docker compose ps`: api, worker, postgres, and redis healthy; judge-runtime running.
- `Invoke-WebRequest -UseBasicParsing http://localhost:8000/api/v1/health`: passed with HTTP 200 and `{"status":"healthy","app":"FastOJ"}`.
- `Invoke-WebRequest -UseBasicParsing http://localhost:8000`: passed with HTTP 200 and returned frontend HTML.
- `uv run ruff check .`: passed after the latest sidebar button and WA compatibility fixes.
- `uv run pytest`: passed after the latest sidebar button and WA compatibility fixes, 66 tests passed with 3 datetime deprecation warnings.
- `cd frontend && npm run build`: passed after the latest sidebar button and WA compatibility fixes, with Monaco/Shiki chunk-size warnings.
- `cd frontend && npm test`: passed after the latest sidebar button and WA compatibility fixes, 6 test files and 8 tests passed; jsdom printed expected canvas `getContext` warnings.
- `docker compose up --build -d`: passed after the latest sidebar button and WA compatibility fixes.
- `docker compose ps`: api, worker, postgres, and redis healthy; judge-runtime running.
- `Invoke-WebRequest -UseBasicParsing http://localhost:8000/api/v1/health`: passed with HTTP 200 and `{"status":"healthy","app":"FastOJ"}`.
- `Invoke-WebRequest -UseBasicParsing http://localhost:8000`: passed with HTTP 200 and returned frontend HTML.
- `uv lock`: passed after adding `requests<2.32`; lock changed `requests` from 2.32.5 to 2.31.0 so Docker SDK 7.0.0 can use the Docker socket.
- `uv sync --extra dev`: passed after the lock update.
- `uv run ruff check .`: passed after Docker executor WIP edits.
- `uv run pytest`: passed after Docker executor WIP edits, 68 tests passed with 3 datetime deprecation warnings.
- `cd frontend && npm run build`: passed after the lock update, with Monaco/Shiki chunk-size warnings.
- `cd frontend && npm test`: passed after the lock update, 6 test files and 8 tests passed; jsdom printed expected canvas `getContext` warnings.
- `docker compose up --build -d`: passed after latest worker/dependency edits.
- Real API submit against Two Sum function mode is fixed after Docker source/stdin injection, seed normalization, and async consumer task-code fixes.
- `docker compose up --build -d`: passed again after Docker Desktop was restarted on 2026-05-14.
- `docker compose ps`: api, worker, postgres, and redis healthy; judge-runtime running.
- `Invoke-WebRequest -UseBasicParsing http://localhost:8000/api/v1/health`: passed with HTTP 200 and `{"status":"healthy","app":"FastOJ"}`.
- `Invoke-WebRequest -UseBasicParsing http://localhost:8000`: passed with HTTP 200 and returned frontend HTML.
- `docker compose exec -T worker uv run python -c "import docker, requests; print(requests.__version__); print(docker.from_env().ping())"`: passed; requests was 2.31.0 and Docker ping returned `True`.
- Real API submit against Two Sum function mode returned `RE`; public testcase result showed `cat: input.txt: No such file or directory` and Python could not open `/tmp/work/solution.py`.
- `uv run ruff check .`: passed after removing legacy function-mode testcase compatibility and adding i18n/problem-set updates.
- `uv run pytest`: passed after removing legacy function-mode testcase compatibility and adding i18n/problem-set updates, 68 tests passed with 3 datetime deprecation warnings.
- `cd frontend && npm run build`: passed after i18n/single mode-toggle/auth redirect/problem-set updates, with Monaco/Shiki chunk-size warnings.
- `cd frontend && npm test`: passed after i18n/single mode-toggle/auth redirect/problem-set updates, 6 test files and 8 tests passed; jsdom printed expected canvas `getContext` warnings.
- `docker compose up --build -d`: passed after latest frontend/i18n and seed-data changes.
- `docker compose ps`: api and worker healthy; postgres and redis healthy; judge-runtime running.
- `Invoke-WebRequest -UseBasicParsing http://localhost:8000/api/v1/health`: passed with HTTP 200 and `{"status":"healthy","app":"FastOJ"}`.
- `Invoke-WebRequest -UseBasicParsing http://localhost:8000`: passed with HTTP 200 and returned frontend HTML.
- `docker compose exec -T api uv run python -m backend.scripts.seed_data`: passed and created 12 missing problems in the current database.
- `docker compose exec -T worker uv run python -c "... SandboxExecutor().execute(...)"`: initially reproduced `Runtime error (exit code 2)` with missing `solution.py`/`input.txt`, then passed after removing tmpfs from Docker archive injection.
- Real API public run for Two Sum function mode initially returned `RE`, then `WA` because the async consumer ignored task `judge_code`; after fixing the consumer to prefer task code and normalizing seed testcase input, the same public run returned `AC`.
- `docker compose build judge-runtime`: passed after changing the judge Dockerfile to copy Python from `python:3.11-slim-bookworm` into `node:24-slim` and install `numpy==2.2.6` plus CPU `torch==2.7.1+cpu`.
- `docker compose up -d`: passed and recreated api, worker, and judge-runtime.
- `docker compose exec -T api uv run python -m backend.scripts.seed_data`: passed and normalized 15 existing problems in the current database.
- `docker compose exec -T worker ... SandboxExecutor`: passed for a Python submission importing both NumPy and PyTorch.
- Real API public run and full submit for Two Sum function mode: passed with `result=ac`.
- Real API public run and full submit for Valid Parentheses ACM mode: passed with `result=ac`.
- AI explain endpoint with `AI_PROVIDER=disabled`: returned HTTP 503 as expected.
- `uv run ruff check .`: passed.
- `uv run pytest`: passed, 69 tests passed with 3 datetime deprecation warnings.
- `cd frontend && npm run build`: passed with existing Monaco/Shiki chunk-size warnings.
- `cd frontend && npm test`: passed, 6 test files and 8 tests passed; jsdom printed expected canvas `getContext` warnings.
- `docker compose exec -T api uv run python -m backend.scripts.seed_data`: passed after expanding bundled problems to at least 10 testcase rows and at least two public samples.
- Real API public run for Softmax Cross Entropy: passed with `result=ac`.
- DeepSeek-compatible AI hint/explain/review calls: passed schema validation after scalar/list normalization; hidden testcase contents were not sent.
- `uv run ruff check .`: passed after latest AI/parser/frontend/testcase edits.
- `uv run pytest`: passed after latest AI/parser/frontend/testcase edits, 71 tests passed with 3 datetime deprecation warnings.
- `cd frontend && npm run build`: passed after latest token-expiry alert and fixed-viewport workbench edits, with existing Monaco/Shiki chunk-size warnings.
- `cd frontend && npm test`: passed after latest frontend edits, 6 test files and 8 tests passed; jsdom printed expected canvas `getContext` warnings.
- `docker compose up --build -d api`: passed and rebuilt/recreated API with the latest frontend bundle.
- `docker compose ps`: API and worker healthy; PostgreSQL and Redis healthy; judge runtime running.
- `Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/v1/health`: passed with HTTP 200 and `{"status":"healthy","app":"FastOJ"}`. In this PowerShell session, `localhost` may time out while `127.0.0.1` works.
- `Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000`: passed with HTTP 200 and returned rebuilt frontend HTML.
- `uv run ruff check .`: passed after account/admin/AI-locale/function-starter edits.
- `uv run pytest`: passed after account/admin/AI-locale/function-starter edits, 72 tests passed with 3 datetime deprecation warnings.
- `cd frontend && npm run build`: passed after account/admin/AI-locale/function-starter edits, with existing Monaco/Shiki chunk-size warnings.
- `cd frontend && npm test`: passed after account/admin/AI-locale/function-starter edits, 6 test files and 8 tests passed; jsdom printed expected canvas `getContext` warnings.
- `docker compose up --build -d api worker`: passed after Docker Desktop was restarted and after the sandbox stdin/permission fixes.
- `docker compose ps`: API and worker healthy; PostgreSQL and Redis healthy; judge runtime running.
- `Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/v1/health`: passed with HTTP 200 and `{"status":"healthy","app":"FastOJ"}`.
- `Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000`: passed with HTTP 200.
- Real Docker-backed public run for Two Sum C++ function mode passed with `result=ac`.

## Failed Commands And Error Summary

- Earlier `uv sync` failed in sandbox due uv cache permission; approved rerun passed.
- Earlier `npm config set save-exact true` failed due user `.npmrc` permission; approved rerun passed.
- Earlier frontend dependency install failed in sandbox cache-only mode; approved network rerun passed.
- Earlier Vite/Vitest runs hit `spawn EPERM`; approved reruns passed.
- Earlier frontend build failed on TypeScript/Vite/Tailwind config issues; fixed and passed.
- Earlier `docker compose up --build -d` failed because Docker Desktop Linux engine was not running.
- Docker then failed because `openjdk-17-jdk-headless` was unavailable on the Debian base image; fixed by using `default-jdk-headless`.
- Docker then failed on flaky Debian apt 502 responses and oversized judge npm dependency chain; fixed by using `node:24-slim` for the judge image and adding apt retries.
- API startup failed against an existing database volume because Alembic tried to create tables that already existed; fixed by adding `backend/scripts/migrate_or_stamp.py`.
- Worker Docker SDK initially failed with `Not supported URL scheme http+docker`; fixed in WIP by pinning `requests<2.32`.
- Real function-mode submissions exposed two issues: tmpfs prevented Docker archive injection from materializing files under Docker Desktop worker-in-container mode, and the async consumer ignored wrapped task code. Both have been fixed.
- A final `docker compose ps` previously failed because Docker Desktop Linux engine pipe was unavailable; after Docker Desktop restart, compose and HTTP health checks passed.
- Recent Docker build attempts failed transiently on Debian mirror 502 responses while trying Debian `python3-torch`/`npm` routes. The final working judge Dockerfile avoids those paths by copying Python from a Python base image and using pip CPU wheels for NumPy/PyTorch.

## Next Minimal Continue Plan

1. Run the browser manual acceptance path at `http://127.0.0.1:8000`, including register/login redirect, token-expiry alert, language switch, sidebar toggles/resizing, function/ACM single-button toggle across languages, public run, full submit, WebSocket/polling status, and DeepSeek AI hint/explain/review in Chinese.
2. Inspect the Chinese UI in a real browser for any remaining mixed-language problem text; move problem statement/solution translations from temporary frontend/backend maps to backend-managed localized fields when the content model is finalized.
3. Expand admin UI beyond basic controls when ready: full problem editor, official-solution editor, and testcase editor that never exposes hidden testcase contents to non-admins and warns before editing hidden data.
4. Expand C function-mode harnesses for AI tasks that require matrices or strings, or hide C function mode for those tasks until supported.
5. Optionally split Monaco/Shiki into lazy chunks to reduce initial frontend bundle size.
