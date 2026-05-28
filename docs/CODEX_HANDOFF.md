# Codex Handoff

Updated: 2026-05-29

## Current Goal

Upgrade the current FastAPI + PostgreSQL + Redis + Docker Worker + static frontend FastOJ prototype into an AI-explainable interview training OJ platform. The target includes AI explanation/review/hints, hidden-test isolation, Redis Streams worker flow, WebSocket-first judge status, Docker sandbox hardening, Vite + React + TypeScript frontend, tests, Docker verification, and README updates.

## 2026-05-29 Workbench Run Panel And Auth Feedback

- Workbench public runs now support editable public run inputs. The new result panel below Monaco shows sample input, official/reference generated expected output, the user's actual output, and line-level diffs with mismatches highlighted.
- Backend public runs accept a bounded `run_testcases` payload containing input only, ignore any client-provided expected output, and persist those results without a testcase foreign key. Hidden/full-submit behavior still uses stored testcases only and no hidden input/expected/actual output is returned.
- Custom public-run expected output is generated server-side by running the official solution in the sandbox when available. `next-permutation`, `diameter-of-binary-tree`, and `maximum-depth-of-binary-tree` also have built-in Python reference generators; exact public sample input can fall back to already visible public sample output.
- Hidden-case WebSocket progress was tightened so full-submit hidden phases do not expose current testcase names, counts, or last-case status metadata.
- The result panel is safe by construction: output/diff content is rendered as text nodes, not injected HTML.
- The editor/result split in the center panel is now vertically resizable, defaults to a taller editor, and persists editor height in localStorage.
- Left/right workbench sidebars now have wider resize hit areas, larger resize ranges, and snap closed only after pointer release when dragged near the edge.
- The left detail dock now places visual guidance and official hints after the public sample cards rather than between sample content.
- The AI Copilot panel now omits the duplicated public-case comparison block; detailed input/expected/actual/diff comparison lives in the run result panel, while AI focuses on cause, suspicious code, boundary checks, and next action. The right AI container also grows with expanded detail content.
- Custom runs for Majority Element now use a built-in sandboxed reference generator, and official function-solution wrapping uses the same function-signature fallback exposed by the problem API.
- Python function mode now detects stale ACM starter drafts cached under the function-mode draft key and restores the function starter; resetting the template also persists the corrected draft.
- Auth now has registration confirm-password validation plus clear success/error dialogs. Registration success shows a dialog before entering the library.
- README and README.zh-CN page descriptions were updated for the current workbench/auth behavior. Screenshot PNG regeneration was attempted but blocked because the available WSL/browser paths had no runnable browser binary and Windows interop failed with `UtilBindVsockAnyPort`.
- Verification on 2026-05-29: `uv run ruff check .` passed; targeted backend tests for judge/function-mode behavior passed; `cd frontend && npm run build` passed; `cd frontend && npm test` passed; `docker compose up --build -d api worker` passed; API health returned `{"status":"healthy","app":"FastOJ"}` at `http://127.0.0.1:8010/api/v1/health`; a real custom-run smoke for Majority Element `[1,2,2]` returned `expected_output: 2`, `actual_output: 2`, and `result: ac`.

## 2026-05-26 Linux/WSL Deployment Pass

- The project now deploys successfully from WSL/Linux with Docker Desktop's Linux engine.
- Compose database credentials and API `SECRET_KEY` are configurable through `.env` while retaining local-development defaults.
- The API service now maps `host.docker.internal` to Docker `host-gateway`, so local OpenAI-compatible model servers on the Linux host can be reached from containers on native Linux as well as Docker Desktop/WSL.
- `.env.example` now includes host-direct development values: PostgreSQL on `localhost:5433`, Redis on `localhost:6379`, safe local secrets, and JSON syntax guidance for list settings such as `CORS_ORIGINS`.
- `Dockerfile.dev` no longer bakes `.env` into the image and starts via `uv run`.
- Python execution now uses `python3` on non-Windows hosts and inside Docker judge execution paths, matching Linux test expectations.
- Frontend metadata now declares Node `^20.19.0 || >=22.12.0` and npm `>=10`.
- English and Chinese READMEs now include Linux/WSL prerequisites, `npm ci` for reproducible frontend installs, direct-backend port guidance, judge runtime build guidance, `host.docker.internal` behavior, and Linux/WSL local Qwen startup/smoke-test commands.
- Verification passed on 2026-05-26: `uv sync --extra dev`, `uv run ruff check .`, `uv run pytest` (96 passed), `cd frontend && npm run build`, `cd frontend && npm test` (8 files / 15 tests passed), `docker compose up --build -d api worker`, `docker compose ps` healthy, `curl --noproxy '*' http://127.0.0.1:8000/api/v1/health`, Docker-served frontend HTML, worker container Docker judge smoke returning `{'status': 'ac', 'output': 'ok\n', ...}`, and `docker compose exec -T api uv run python -m backend.scripts.seed_data` normalizing 106 problems.

## 2026-05-18 Hot 100 Seed Catalog Expansion

- The bundled seed catalog now contains all 100 canonical Hot 100 practice problems plus the existing 6 AI/ML exercises, for 106 total seeded problems.
- New Hot 100 metadata lives in `backend/scripts/hot100_data.py`; statements are FastOJ-original summaries, and linked-list, tree, design, and multi-answer tasks use deterministic ACM input/output conventions.
- The legacy `longest-substring-without-repeating` seed slug is now migrated to canonical `longest-substring-without-repeating-characters` during seed upsert, with backend function-mode and frontend starter/localization aliases to avoid breaking existing behavior.
- New regression coverage in `tests/test_seed_catalog.py` verifies Hot 100 coverage, slug uniqueness, and canonical slug behavior.
- Verification passed: `uv run ruff check .`, `uv run pytest` (96 passed), `cd frontend && npm run build`, `cd frontend && npm test` (8 files / 15 tests passed), Docker seed execution, database count check (106 problems / 1060 testcase rows), and HTTP health at `http://127.0.0.1:8000/api/v1/health`.
- Direct local `uv run python -m backend.scripts.seed_data` failed before Docker verification because psycopg2 hit a Windows localized connection-error decoding issue. The same seed script passed in the intended Docker API container after starting `docker compose up -d api`.

## 2026-05-17 DeepSeek Authoring And Library Layout Follow-up

- Follow-up addressed two user-reported issues: DeepSeek v4 generated drafts showing only `validation_failed`, and the problem library needing an OJ-style one-row layout in addition to the current card grid.
- Function-mode draft validation now accepts common AI-generated argument shapes: newline-separated JSON values, a single JSON array matching all function arguments, or a single JSON object keyed by argument names.
- The approved dynamic Python function-mode submission wrapper now uses the same argument-shape handling, so drafts that validate under the new shape rules are judged with matching runtime semantics.
- Problem-authoring prompts now explicitly require function-mode outputs to be JSON-serializable return values and ask combination/set-like problems to use deterministic canonical ordering.
- Validation reports now include a safe `case_summary` and sanitize executor error detail so hidden testcase input, expected output, actual output, and stderr-derived values are not persisted or rendered through the validation path.
- The admin Problem Agent panel now renders validation as a human-readable safe summary: failed checks, public/hidden counts, failed-case counts, and sandbox statuses, instead of a raw JSON dump and `validation_failed: validation_failed`.
- The problem library now has a persisted card/list layout toggle. List mode renders one problem per row with title/slug, difficulty, tags, supported modes, solved/submission count, acceptance rate, and open action.
- Full verification passed for this follow-up: `uv run ruff check .`, `uv run pytest` (92 passed), `cd frontend && npm run build`, `cd frontend && npm test` (8 files / 13 tests passed), `docker compose up --build -d api worker`, `docker compose ps`, and HTTP health at `http://127.0.0.1:8000/api/v1/health`.
- Browser smoke against the real Docker-served app verified the library card/list toggle, 15 rendered list rows, 15 rendered cards after toggling back, no horizontal overflow, and no visible `[object Object]` or hidden-test sentinel text. Screenshot capture still timed out on CDP `Page.captureScreenshot`.

## 2026-05-17 Acceptance/Product Batch

- Dynamic orchestration used specialist subagents for code mapping, product planning, frontend design planning, acceptance harness planning, and safety/privacy review. The safety review made stale AI state and raw error stringification no-go items; both were addressed before handoff.
- Added a manual acceptance harness at `docs/ACCEPTANCE_HARNESS.md`. It records the automated baseline, browser smoke matrix, screenshot inventory, safety checks, and future Playwright structure without adding new dependencies.
- Frontend API errors are now sanitized through `formatApiErrorResponse`/`formatApiErrorDetail`, with tests covering FastAPI validation arrays and suspicious structured payloads.
- AI problem-authoring draft validation errors now report field path/type summaries instead of raw Pydantic exception text, with a regression test ensuring secret-like draft values are not echoed.
- Library search now has localized public-problem matching helpers, with tests proving Chinese `两数之和` and English `Two Sum` both match the seeded Two Sum card.
- Workbench judge/AI state is isolated by current problem/submission. New runs/submissions clear stale AI panels, stop old status streams, and ignore late WebSocket, polling, explain, review, hint, or chat callbacks from stale submissions.
- Workbench 1280px overflow was fixed by clamping grid panel tracks; browser smoke reported no horizontal overflow.
- Core visual tokens were added in CSS for color, radius, border depth, shadows, focus rings, status colors, and AI glow. Buttons, inputs, library cards, workbench panels, settings/admin/auth shells, and AI regions now use stronger soft neo-brutalist panel depth.
- Browser smoke after rebuild inspected the real Docker-served UI at `http://127.0.0.1:8000`: library and workbench rendered, workbench at 1280px had no horizontal overflow, public run produced a visible result, no `[object Object]` appeared, no hidden testcase content appeared in the observed run result, and AI provider error state cleared when a new run started.
- Final screenshot capture after the last CSS rebuild timed out in the browser plugin, but earlier library/workbench screenshots were captured during the audit and final DOM/layout checks confirmed the rebuilt CSS tokens were loaded.

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
- Seed data now appends missing problems by slug and includes the full canonical Hot 100 track plus AI algorithm practice tasks for logistic regression sigmoid, KNN, KMeans, scaled dot-product attention, softmax cross entropy, and attention mask application.
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
- Admin bootstrap script added at `backend/scripts/create_admin.py`; it creates or promotes the first administrator from a trusted server shell, uses existing password hashing, requires exact username/email matches for promotion, and does not allow public self-service role assignment.
- Obsolete static frontend prototype files and stale Codex checkpoint artifacts were removed after their useful context was consolidated into committed code and handoff/progress docs.
- The Qwen local profile now has a local OpenAI-compatible service pattern: install `llama-server` b9060 and Qwen2.5-Coder-7B-Instruct Q4_K_M outside the repo under `%USERPROFILE%\Models\qwen`, listen on `http://127.0.0.1:8080/v1`, and let Docker containers call it through `http://host.docker.internal:8080/v1`. Reusable local scripts can live at `%USERPROFILE%\Models\qwen\start-qwen-llama-server.ps1` and `%USERPROFILE%\Models\qwen\stop-qwen-llama-server.ps1`.

## Not Completed Yet

- Full browser manual acceptance path is partially executed and now documented, but it is not yet automated as a Playwright/equivalent suite.
- WebSocket fallback behavior has not been verified in a real browser session.
- Real Redis dead-letter behavior is covered by unit-level tests but not manually exercised end to end.
- Frontend bundle size is large because Monaco and Shiki are loaded directly.
- Function mode wrappers now support Python, C++, Java, JavaScript, TypeScript, Go, and selected simpler C signatures. C still needs expanded matrix/string harnesses for some AI tasks.
- Approved Python function-mode Agent drafts now carry dynamic function metadata into the public problem API, workbench starter generation, and submission wrapper. Non-Python arbitrary function-mode harness metadata is still not implemented; those drafts fail validation instead of being published as runnable function tasks.
- Docker sandbox compiled-language execution now redirects `input.txt` into the final program instead of piping it into the compiler, and `/tmp/work` permissions are relaxed with `chmod` so `nobody` can create compiled binaries without adding Linux capabilities.
- Docker Compose rebuild passed after the latest worker/dependency edits. After Docker Desktop was restarted on 2026-05-14, API and worker reported healthy, HTTP health and frontend returned 200, and worker-in-container Docker SDK access returned `True`.
- The final CSS rebuild was verified by DOM/layout checks; a final screenshot attempt timed out in the browser plugin. Earlier library/workbench screenshots were captured during this batch.

## Current Modified File List

Modified and new files after the latest admin-agent, acceptance, and frontend polish work include backend admin/admin-agent routes, `backend/services/problem_authoring_agent.py`, frontend API/i18n/main/styles files, frontend API/i18n tests, backend problem-authoring tests, README files, `docs/ACCEPTANCE_HARNESS.md`, and Codex handoff/progress docs. Removed files from earlier cleanup included obsolete static frontend prototype files and stale checkpoint/recovery artifacts.

## Executed Commands And Results

- `uv run ruff check .`: passed after the 2026-05-17 batch.
- `uv run pytest`: passed after the 2026-05-17 batch, 87 tests passed with existing datetime deprecation warnings.
- `cd frontend && npm run build`: passed after frontend API/i18n/state/CSS edits, with existing Monaco/Shiki chunk-size warnings.
- `cd frontend && npm test`: passed, 8 test files and 13 tests passed; jsdom printed expected canvas `getContext` warnings.
- `docker compose up --build -d api worker`: passed after the 2026-05-17 batch.
- `docker compose ps`: passed after rebuild; API and worker healthy, PostgreSQL/Redis healthy, judge runtime running.
- `Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/v1/health`: passed with HTTP 200 and `{"status":"healthy","app":"FastOJ"}`.
- `docker compose exec -T api uv run python -m backend.scripts.seed_data`: passed, created 0 missing problems and normalized 15 existing problems.
- Browser smoke at `http://127.0.0.1:8000`: passed for rendered library/workbench inspection, 1280px workbench overflow check, public run result visibility, stale AI error clearing on a new run, no `[object Object]`, and no visible hidden testcase content in the observed run result.
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
- Local Qwen deployment smoke: `llama-server` `/v1/models` and `/v1/chat/completions` passed on `127.0.0.1:8080`; Docker API reached the service via `host.docker.internal`; FastOJ `model_profile=qwen-local` AI hint passed through the HTTP API after temporary user registration/login.
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

- One `uv run ruff check .` run failed on UP038 for `isinstance(nested, (dict, str))`; changed it to `isinstance(nested, dict | str)` and reran ruff successfully.
- One sandboxed `docker compose ps` check hit Docker pipe permission denial; reran the Docker status check with approved escalation and confirmed healthy services.
- Browser `fill`/`type` for Chinese search was blocked by the Browser virtual clipboard not being installed. The localized search behavior is covered by frontend unit tests; the rendered Chinese library was still inspected in the browser.
- A final browser screenshot attempt after the last CSS rebuild timed out on CDP `Page.captureScreenshot`; earlier library/workbench screenshots were captured during the audit, and final DOM/layout checks verified the rebuilt CSS state.
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

1. Convert `docs/ACCEPTANCE_HARNESS.md` into a Playwright/equivalent browser suite covering auth, library search/filter, function and ACM run/submit, WebSocket-first status, polling fallback, AI locale behavior, settings, admin, and screenshot smoke.
2. Finish the remaining browser manual acceptance items not fully automated in this batch: register/login redirect, token-expiry alert, settings save/error with typed form data, admin mutation restore paths, and explicit polling fallback simulation.
3. Inspect the Chinese UI in a real browser for any remaining mixed-language problem text; move problem statement/solution translations from temporary frontend/backend maps to backend-managed localized fields when the content model is finalized.
4. Expand admin UI beyond basic controls when ready: full problem editor, official-solution editor, testcase manager with hidden-content safeguards, submission audit, judge queue, and system health.
5. Expand C function-mode harnesses for AI tasks that require matrices or strings, or hide C function mode for those tasks until supported.
6. Split Monaco/Shiki into lazy chunks to reduce initial frontend bundle size.
