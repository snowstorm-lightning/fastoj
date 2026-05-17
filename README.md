# FastOJ

English | [简体中文](README.zh-CN.md)

FastOJ is an AI-explainable interview training OJ platform. It keeps traditional OJ judging strictness while making judge explanations, code review, progressive hints, judge timelines, training graphs, and submission trails first-class user experiences.

AI explanations are grounded in the real submission verdict and public testcase information. Hidden testcase input, expected output, and actual output are never returned to normal users and are never sent to the AI provider.

## Architecture

- Backend: FastAPI, SQLAlchemy 2.0, PostgreSQL, Alembic, JWT auth.
- Queue: Redis Streams with consumer groups, ack, retry, dead-letter, and pending reclaim.
- Judge: Docker sandbox worker. Production does not fall back to host subprocess execution.
- Realtime: Worker publishes status events to Redis pub/sub; API relays events to WebSocket clients.
- Frontend: Vite, React, TypeScript, Tailwind CSS, Monaco Editor, TanStack Query, Zustand, Zod, xterm, Shiki, @xyflow/react, @chenglou/pretext. The UI is organized as a three-view training flow: problem library, core function-mode workbench, and training graph.
- AI: OpenAI-compatible chat completions provider, disabled by default.

## Dependency Audit

Phase 0 audit results are recorded in `docs/dependency-audit.md`.

Verified locally:

- Python 3.12.10
- uv 0.10.2
- Node.js v24.15.0
- npm 11.12.1
- Docker 29.2.1
- Docker Compose v5.1.0

## Backend Startup

```bash
uv sync --extra dev
uv run alembic -c backend/alembic.ini upgrade head
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

For local development only, you may initialize tables by running the API with `DEBUG=true`; production should use Alembic migrations instead of unconditional `Base.metadata.create_all()`.

Create the first administrator from a trusted server shell after migrations:

```bash
uv run python -m backend.scripts.create_admin --username admin --email admin@example.com
```

For the Docker Compose stack, run the same bootstrap inside the API container so it uses the container database settings:

```bash
docker compose exec api uv run python -m backend.scripts.create_admin --username admin --email admin@example.com
```

The script prompts for the password without echoing it. For non-interactive environments, set `FASTOJ_ADMIN_PASSWORD` in the trusted execution environment instead of passing secrets through shell history. Existing users can be promoted only when both username and email match; use `--reset-password` explicitly if an existing admin password should be rotated.

## Frontend Startup

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies API calls by using the same origin unless `VITE_API_BASE_URL` is configured.

## Frontend Experience

The React frontend is intentionally split into focused views instead of one dense all-in-one page:

- Problem library: keyword, tag, difficulty, pagination, training summary, AI-practice count, function-mode count, recommendation entry, and a persisted card/list layout toggle. The list layout is a classic OJ-style one-row-per-problem view with difficulty, tags, modes, solved count, and acceptance rate.
- Auth flow: login and registration live on a dedicated page instead of being embedded in the global header.
- Workbench: a focused three-column layout with collapsible and resizable problem/result sidebars, central Monaco editor, and a right-side AI/judge drawer.
- Mode switch: supported problems can run in `function` mode, where the editor shows a language-specific function signature and the backend wraps it in a stdin/stdout harness before judging. All problems can still use `acm` mode, where the submission owns standard input and output. The workbench uses one compact toggle button with localized text and mode-colored status dots.
- Language switch: the current UI ships a frontend-side Chinese/English catalog for navigation, auth, verdict labels, hover explanations, mode labels, and seeded problem display text. Longer term, user-authored domain content such as problem statements and official solutions should move to backend-managed localized fields while stable UI chrome stays in the frontend i18n bundle.
- Detail dock: public cases, official solution, judge terminal, submission trail, and local discussion are available as tabs.
- Training graph: @xyflow/react renders knowledge nodes; clicking a node returns to the library and applies the tag filter.
- Static visual guide: supported problems render a prebuilt visual step flow in the statement sidebar, avoiding runtime AI calls for basic conceptual explanation.
- Button clarity: primary workflow buttons use icon-first controls, custom hover popovers, and 3D normal/hover/pressed states. Collapsed sidebars use compact edge controls.
- Token expiry: if a submit action discovers an expired session, the frontend shows a localized expiry alert before redirecting to the dedicated auth page.
- Error surfaces: FastAPI validation errors are summarized as field/type messages instead of raw objects, so auth/settings/admin failures do not render `[object Object]` or stringify structured payloads.
- Localized search: the Chinese library can match localized seeded problem titles such as `两数之和` while keeping search scoped to public problem metadata.
- AI model selection: the workbench can choose a controlled AI profile (`default`, `deepseek`, or `qwen-local`) without exposing arbitrary model names or base URLs to the browser.
- AI state isolation: new runs, new submissions, and problem switches clear stale hint/explain/review/chat state, and late status/AI callbacks are ignored if they belong to an older submission.
- Account settings: signed-in users can edit display name, username, email, avatar URL, compact mode, and password.
- Admin console: server-side admin role checks protect user and problem management. The UI can change user role/active state, problem difficulty/public state, and create a missing Python official-solution placeholder without exposing hidden testcase content. Problem-authoring draft validation is shown as a safe summary of failed checks, public/hidden counts, failed-case counts, and sandbox statuses instead of raw testcase or stderr payloads.
- Admin provisioning: public registration always creates a normal `user`; administrator accounts are bootstrapped with `backend.scripts.create_admin` or managed by an existing admin from the console.

AI Copilot defaults to the current verdict and next action. Longer information such as suspicious code regions, public-case comparison, boundary checks, and complexity notes is placed in expandable sections to reduce cognitive load.

The current visual system uses local CSS design tokens for panel radius, strong borders, offset shadows, status colors, focus states, and restrained AI glow. The direction is soft neo-brutalism adapted to a dark AI/OJ workbench rather than a generic marketing page.

## Pretext Text Layout

Business components should not call `@chenglou/pretext` directly. Use `frontend/src/lib/textLayout.ts`, which wraps:

- `prepareWithSegments`
- `measureNaturalWidth`
- `measureLineStats`
- `layoutWithLines`

Current users of the adapter:

- problem cards, for stable card height around mixed title/tag text
- training graph nodes, for node label sizing
- submission trail summaries, for dense attempt text layout

If Pretext measurement fails, the adapter falls back to deterministic approximate dimensions so UI rendering is not blocked.

## Docker Compose

```bash
docker compose up --build
```

Services:

- `postgres`: PostgreSQL database.
- `redis`: queue and judge status bus.
- `api`: FastAPI plus built frontend static assets.
- `worker`: Redis Streams judge worker.
- `judge-runtime`: builds and keeps the `fastoj-judge:latest` sandbox runtime image available.

The API container runs `python -m backend.scripts.migrate_or_stamp` before starting. New databases run Alembic normally. Existing prototype databases that already have core tables but no `alembic_version` are stamped to the baseline revision before startup, so local Docker volumes are not destroyed or recreated.

## Database Migration

```bash
uv run alembic -c backend/alembic.ini upgrade head
uv run alembic -c backend/alembic.ini revision --autogenerate -m "message"
```

Production deployments should run migrations explicitly. Development may use `DEBUG=true` table creation for quick local experiments, but that is not recommended for production.

## Judge Worker

Submissions are enqueued into Redis Stream `judge:tasks`. Workers use consumer group `judge-workers`, acknowledge completed messages, retry failed messages up to `JUDGE_TASK_MAX_RETRIES`, and move exhausted tasks into `judge:dead-letter`.

Duplicate tasks are safe: a worker checks whether a submission is already finished with testcase results before writing another result batch.

## Sandbox Security

Production uses Docker sandbox execution only. If Docker is unavailable, submissions return a system error unless:

```bash
FASTOJ_ALLOW_UNSAFE_LOCAL_EXECUTION=true
```

That option is only for local development and must not be enabled in production.

Sandbox containers are configured with:

- network disabled
- memory and memswap limits
- pids limit
- `cap_drop=["ALL"]`
- `no-new-privileges`
- code and stdin copied into an isolated ephemeral container working directory through the Docker API
- non-root user
- output truncation
- timeout kill and cleanup

MLE detection depends on Docker exit/status behavior and may be reported as MLE or system error depending on runtime details.

## WebSocket Realtime Judging

Clients connect to:

```text
/ws/judge/{submission_id}?token={JWT}
```

The frontend shows Pending immediately, then prefers WebSocket events. If the socket fails or disconnects, it polls:

```text
GET /api/v1/submissions/{submission_id}
```

Status event types include `pending`, `judging`, `progress`, `result`, and `error`.

## AI Features

AI is disabled by default:

```bash
AI_PROVIDER=disabled
```

When disabled, AI endpoints return HTTP 503 and the core OJ flow still works.

Endpoints:

- `POST /api/v1/ai/submissions/{submission_id}/explain`
- `POST /api/v1/ai/submissions/{submission_id}/review`
- `POST /api/v1/ai/problems/{problem_id}/hint`

Admin Problem Authoring Agent endpoints are also available under `/api/v1/admin` for administrators only:

- `POST /api/v1/admin/agent/problem-drafts`
- `GET /api/v1/admin/agent/runs/{run_id}`
- `GET /api/v1/admin/problem-drafts`
- `GET /api/v1/admin/problem-drafts/{draft_id}`
- `POST /api/v1/admin/problem-drafts/{draft_id}/approve`
- `POST /api/v1/admin/problem-drafts/{draft_id}/reject`

The agent stores generated content as `ProblemDraft` rows with `AgentRun` and `AgentStep` traces. Draft approval is a separate admin action that creates the public `Problem`, `TestCase`, and official `Solution` rows. AI-generated problems are never published automatically. Draft validation checks required fields, slug uniqueness, testcase counts, non-empty expected outputs, function-mode argument shape, and the official solution through the sandbox validation adapter. ACM drafts use the existing sandbox executor directly. Python function-mode drafts store their function signature on the approved problem, render a dynamic starter in the workbench, and run through the same dynamic harness during submission. The dynamic Python harness accepts newline-separated JSON argument values, a single JSON array matching all arguments, or a single JSON object keyed by argument name, which makes DeepSeek-style generated drafts less brittle while preserving deterministic judging.

Rules:

- AI explain/review require login.
- Users may explain/review only their own submissions; admins may access all.
- Hidden testcase input, expected output, and actual output are never included in AI prompts.
- If a hidden testcase fails, the AI context only says hidden data cannot be shown and suggests boundary categories.
- The AI is instructed not to reveal complete accepted solutions.
- AI responses receive the active UI locale (`zh` or `en`) and should render in the same language as the page.
- Provider JSON is normalized before schema validation, so common OpenAI-compatible variations such as scalar `focus`, `risks`, or verdict strings do not break hint, explanation, or review rendering.

FastOJ uses one OpenAI-compatible provider path for both hosted API models and local models. Store secrets in the repository-root `.env` file or in deployment environment variables. The root `.env` and `.env.*` files are ignored by git; `.env.example` is safe to commit and documents the expected variable names.

## Admin Account Security

- Public registration never accepts a role field and stores new accounts as `user`.
- Admin-only APIs use server-side `require_admin` checks under `/api/v1/admin`; hiding links in the frontend is not the security boundary.
- Passwords are stored as salted PBKDF2-HMAC-SHA256 hashes through `backend.core.security.get_password_hash`; plaintext admin passwords are not stored.
- Login issues short-lived access JWTs plus refresh tokens signed with `SECRET_KEY`; disabled users cannot log in.
- The first admin is created from a trusted shell with `uv run python -m backend.scripts.create_admin --username admin --email admin@example.com`, or with `docker compose exec api uv run python -m backend.scripts.create_admin --username admin --email admin@example.com` when using the Compose stack. The script enforces a minimum 12-character password, promotes only an exact username/email match, and requires `--reset-password` before replacing an existing password.
- Existing admins can change user roles and active state from the admin console. Removing the last usable admin is an operational risk, so keep at least one break-glass admin account or retain server shell access for the bootstrap script.

DeepSeek API mode:

```bash
AI_PROVIDER=openai_compatible
AI_BASE_URL=https://api.deepseek.com
AI_API_KEY=your-deepseek-api-key
AI_MODEL=deepseek-v4-flash
```

DeepSeek's official docs list `https://api.deepseek.com` as the OpenAI-format base URL and current models such as `deepseek-v4-flash` and `deepseek-v4-pro`. The legacy names `deepseek-chat` and `deepseek-reasoner` are documented as compatibility aliases that will be deprecated later.

## Practice Modes And Seed Problems

Seed data can be applied to a new or existing database. Existing seeded problems are normalized by slug so old prototype testcase rows are updated to the current JSON-line format without deleting historical submission records:

```bash
uv run python -m backend.scripts.seed_data
```

The seed set includes traditional interview tasks, selected interview-list practice tasks, and AI algorithm tasks:

- Traditional/function tasks: Two Sum, Add Two Numbers, Longest Substring Without Repeating Characters.
- Interview-list ACM tasks: Valid Parentheses, Maximum Subarray, Group Anagrams, Merge Intervals, Climbing Stairs, Container With Most Water.
- AI algorithm tasks: Logistic Regression Sigmoid, KNN Majority Vote, KMeans One Iteration, Scaled Dot-Product Attention, Softmax Cross Entropy, Attention Mask Apply.

Function mode supports Python, C++, Java, JavaScript, TypeScript, Go, and selected C wrappers for seeded function tasks. ACM mode remains available for every problem and language.

Function-mode testcase data uses the current JSON-line format only. Incompatible prototype testcase rows are normalized by the seed script instead of being supported by extra parser compatibility.

The seed script now expands every bundled problem to at least 10 testcase rows and keeps at least two public sample cases where available. Hidden testcase contents remain server-side only.

The Docker judge runtime includes Python `numpy==2.2.6` and CPU `torch==2.7.1+cpu`, so AI algorithm submissions may use either standard Python, NumPy, or PyTorch. These packages live in the judge image rather than the API/worker Python environment because they are needed for submitted code execution, not for request handling.

## llama.cpp Local Model

Recommended runtime:

```bash
llama-server -m %USERPROFILE%\Models\qwen\models\qwen2.5-coder-7b-instruct-q4_k_m.gguf \
  --host 127.0.0.1 \
  --port 8080 \
  --alias qwen2.5-coder-7b-instruct-q4_k_m \
  --ctx-size 4096 \
  --n-gpu-layers 99 \
  --parallel 1
```

Recommended models:

- Low resource: Qwen2.5-Coder-1.5B-Instruct-GGUF, Q4_K_M or similar 4-bit quantization.
- Default quality: Qwen2.5-Coder-3B-Instruct-GGUF, Q4_K_M or similar 4-bit quantization.
- Current local deployment pattern: Qwen2.5-Coder-7B-Instruct-GGUF Q4_K_M stored outside the repo under `%USERPROFILE%\Models\qwen`. Reusable local start/stop scripts can live at `%USERPROFILE%\Models\qwen\start-qwen-llama-server.ps1` and `%USERPROFILE%\Models\qwen\stop-qwen-llama-server.ps1`.

FastOJ configuration:

```bash
AI_PROVIDER=openai_compatible
AI_BASE_URL=http://localhost:8080/v1
AI_API_KEY=sk-no-key-required
AI_MODEL=qwen2.5-coder-7b-instruct-q4_k_m
```

In Docker Compose on Docker Desktop, use:

```bash
AI_BASE_URL=http://host.docker.internal:8080/v1
```

For the in-page `Qwen local` selector, keep `AI_PROVIDER=openai_compatible` and set the named profile:

```bash
AI_QWEN_BASE_URL=http://host.docker.internal:8080/v1
AI_QWEN_API_KEY=sk-no-key-required
AI_QWEN_MODEL=qwen2.5-coder-7b-instruct-q4_k_m
```

If the local Qwen server is not running or the port is wrong, AI actions return HTTP 503 with a clear provider-unreachable message instead of a generic server error.

The `DeepSeek` selector uses:

```bash
AI_DEEPSEEK_BASE_URL=https://api.deepseek.com
AI_DEEPSEEK_API_KEY=your-deepseek-api-key
AI_DEEPSEEK_MODEL=deepseek-v4-flash
```

## Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql://fastoj:fastoj_secret@localhost:5432/fastoj` | PostgreSQL DSN |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis DSN |
| `SECRET_KEY` | development placeholder | JWT signing secret |
| `JUDGE_ASYNC` | `false` | Queue judging through Redis worker |
| `JUDGE_CONTAINER_IMAGE` | `fastoj-judge:latest` | Docker judge runtime image |
| `FASTOJ_ALLOW_UNSAFE_LOCAL_EXECUTION` | `false` | Local-only subprocess fallback |
| `JUDGE_MAX_OUTPUT_BYTES` | `65536` | stdout/stderr truncation limit |
| `AI_PROVIDER` | `disabled` | `disabled` or `openai_compatible` |
| `AI_BASE_URL` | `http://localhost:8080/v1` | OpenAI-compatible base URL |
| `AI_API_KEY` | `sk-no-key-required` | Provider API key |
| `AI_MODEL` | `qwen2.5-coder-7b-instruct-q4_k_m` | Chat model |
| `AI_DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | Named DeepSeek profile base URL |
| `AI_DEEPSEEK_API_KEY` | empty | Named DeepSeek profile API key |
| `AI_DEEPSEEK_MODEL` | `deepseek-v4-flash` | Named DeepSeek profile model |
| `AI_QWEN_BASE_URL` | `http://host.docker.internal:8080/v1` | Named local Qwen profile base URL for Docker Desktop |
| `AI_QWEN_API_KEY` | `sk-no-key-required` | Named local Qwen profile API key |
| `AI_QWEN_MODEL` | `qwen2.5-coder-7b-instruct-q4_k_m` | Named local Qwen profile model |
| `AI_TIMEOUT_SECONDS` | `60` | AI request timeout |
| `AI_MAX_OUTPUT_TOKENS` | `1200` | AI response token cap |

## Test Commands

Backend:

```bash
uv sync --extra dev
uv run ruff check .
uv run pytest
```

Frontend:

```bash
cd frontend
npm install
npm run build
npm test
```

Docker:

```bash
docker compose up --build
```

Latest verification from this workspace:

- `uv run ruff check .`: passed.
- `uv run pytest`: passed, 92 tests passed; existing timezone deprecation warnings remain in older tests and service timestamp code.
- `cd frontend && npm run build`: passed after design-token, localized-search, and stale AI-state edits, with existing Monaco/Shiki chunk-size warnings.
- `cd frontend && npm test`: passed, 8 test files and 13 tests passed; jsdom printed expected canvas `getContext` warnings.
- `docker compose build judge-runtime`: passed after adding NumPy and CPU PyTorch to the judge image.
- `docker compose up --build -d api`: passed and rebuilt/recreated the API container with the latest frontend bundle.
- `docker compose ps`: API and worker healthy; PostgreSQL and Redis healthy; judge runtime running.
- `Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/v1/health`: passed with HTTP 200 and `{"status":"healthy","app":"FastOJ"}`. In this PowerShell session, `localhost` can time out even while Docker reports the API healthy, so use `127.0.0.1` for manual checks if needed.
- `Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000`: passed with HTTP 200 and returned rebuilt frontend HTML.
- `docker compose config`: passed.
- `docker compose up --build -d api worker`: passed after admin bootstrap and cleanup work; API and worker are healthy.
- `docker compose up --build -d api worker`: passed after the acceptance-harness and frontend polish batch; API and worker are healthy.
- `docker compose up --build -d api worker`: passed after the DeepSeek authoring and library-layout follow-up; API and worker are healthy.
- Browser smoke at `http://127.0.0.1:8000`: verified the real rendered library card/list toggle, list mode with 15 one-row problem entries, card mode with 15 cards, no horizontal overflow, no `[object Object]`, and no visible hidden-test sentinel text. Screenshot capture still timed out in the browser plugin.
- Browser smoke at `http://127.0.0.1:8000`: inspected the real rendered library and workbench at 1280px, captured library/workbench screenshots during the audit, confirmed no horizontal workbench overflow, no `[object Object]`, no visible hidden-test content in the run result, and AI error state clearing on a new run.
- Docker-backed public run for Two Sum C++ function mode passed with `result=ac` after fixing compiled-language stdin redirection and sandbox workspace permissions.
- Frontend build/test and backend tests passed after the model selector, localized graph, structured sample cards, discussion/settings views, and acceptance-rate clamping work.
- Local Qwen deployment: `llama-server` b9060 was installed outside the repo under a user-level `%USERPROFILE%\Models\qwen` directory, Qwen2.5-Coder-7B-Instruct Q4_K_M was stored in that external model directory, and `/v1/models` plus `/v1/chat/completions` passed smoke tests on `http://127.0.0.1:8080/v1`.
- FastOJ API smoke with `model_profile=qwen-local`: temporary user registration/login, public problem lookup, and AI hint request passed against the Docker API using `http://host.docker.internal:8080/v1`.
- `docker compose exec -T api uv run python -m backend.scripts.seed_data`: passed and normalized 15 existing problems in the current database; all bundled problems now have at least 10 testcase rows and at least two public samples.
- `docker compose exec -T worker ... SandboxExecutor`: passed for a Python submission importing both NumPy and PyTorch.
- Real API public run and full submit for Two Sum function mode passed with `result=ac`; the old `Runtime error (exit code 2)` path is fixed.
- Real API public run and full submit for Valid Parentheses ACM mode passed with `result=ac`.
- Real API public run for Softmax Cross Entropy passed with `result=ac`; an incorrect seeded expected output was corrected without exposing hidden testcase contents.
- DeepSeek-compatible AI hint, failed-submission explanation, and code review calls returned schema-valid responses after scalar/list normalization. Hidden testcase contents were not sent.
- AI explain/review now tolerates provider `null` text fields, local Qwen connection failures return HTTP 503 with a readable provider-unreachable message, and the workbench includes an AI chat endpoint that uses only public submission context.
- Problem cards now show both supported modes; `Valid Parentheses` has function-mode starters and backend wrapper coverage in addition to ACM mode.

## Manual Acceptance Path

The repeatable acceptance harness is recorded in [`docs/ACCEPTANCE_HARNESS.md`](docs/ACCEPTANCE_HARNESS.md). It covers the required automated baseline, browser smoke matrix, screenshot inventory, hidden-test safety checks, and the Playwright automation roadmap without adding a new browser-test dependency in this batch.

1. Open the frontend.
2. Register and log in.
3. Browse the problem library.
4. Filter by keyword, tag, and difficulty.
5. Open a problem workbench.
6. Select a language.
7. Write code or use the template.
8. Run public cases.
9. Submit full judging.
10. Observe Pending -> Judging -> Result status.
11. Explain a failed submission.
12. Run AI code review.
13. Request level 1, 2, and 3 hints.
14. Open the training graph and click a tag node to filter the library.
15. Review the submission trail from the workbench detail dock.
16. Confirm hidden testcase details are not exposed.

## Known Limits

- The bundled frontend currently uses Monaco and Shiki directly, so production chunks are large.
- C function-mode wrappers currently cover only the simpler seeded signatures; use ACM mode for C on AI tasks that require matrices or strings until those C harnesses are expanded.
- MLE classification depends on Docker runtime exit behavior.
- AI quality depends on the configured OpenAI-compatible model.
- The AI review UI is submission-oriented; reviewing unsaved code is implemented through the latest run/submission flow.
- The initial Alembic migration is a baseline for the current schema and should be validated against existing production databases before rollout.
