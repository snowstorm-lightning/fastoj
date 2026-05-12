# FastOJ

FastOJ is an AI-explainable interview training OJ platform. It keeps traditional OJ judging strictness while making judge explanations, code review, progressive hints, judge timelines, training graphs, and submission trails first-class user experiences.

AI explanations are grounded in the real submission verdict and public testcase information. Hidden testcase input, expected output, and actual output are never returned to normal users and are never sent to the AI provider.

## Architecture

- Backend: FastAPI, SQLAlchemy 2.0, PostgreSQL, Alembic, JWT auth.
- Queue: Redis Streams with consumer groups, ack, retry, dead-letter, and pending reclaim.
- Judge: Docker sandbox worker. Production does not fall back to host subprocess execution.
- Realtime: Worker publishes status events to Redis pub/sub; API relays events to WebSocket clients.
- Frontend: Vite, React, TypeScript, Tailwind CSS, Monaco Editor, TanStack Query, Zustand, Zod, xterm, Shiki, @xyflow/react, @chenglou/pretext.
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

## Frontend Startup

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies API calls by using the same origin unless `VITE_API_BASE_URL` is configured.

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

The API container runs `alembic upgrade head` before starting.

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
- read-only root filesystem
- read-only source mount
- tmpfs working directories
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

Rules:

- AI explain/review require login.
- Users may explain/review only their own submissions; admins may access all.
- Hidden testcase input, expected output, and actual output are never included in AI prompts.
- If a hidden testcase fails, the AI context only says hidden data cannot be shown and suggests boundary categories.
- The AI is instructed not to reveal complete accepted solutions.

## llama.cpp Local Model

Recommended runtime:

```bash
llama-server -m /models/qwen2.5-coder-3b-instruct-q4_k_m.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  -c 8192 \
  -np 2
```

Recommended models:

- Low resource: Qwen2.5-Coder-1.5B-Instruct-GGUF, Q4_K_M or similar 4-bit quantization.
- Default quality: Qwen2.5-Coder-3B-Instruct-GGUF, Q4_K_M or similar 4-bit quantization.

FastOJ configuration:

```bash
AI_PROVIDER=openai_compatible
AI_BASE_URL=http://localhost:8080/v1
AI_API_KEY=sk-no-key-required
AI_MODEL=qwen2.5-coder-3b-instruct
```

In Docker Compose on Docker Desktop, use:

```bash
AI_BASE_URL=http://host.docker.internal:8080/v1
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
| `AI_MODEL` | `qwen2.5-coder-3b-instruct` | Chat model |
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

## Manual Acceptance Path

1. Open the frontend.
2. Register and log in.
3. Browse the problem console.
4. Filter by keyword, tag, and difficulty.
5. Open a problem workspace.
6. Select a language.
7. Write code or use the template.
8. Run public cases.
9. Submit full judging.
10. Observe Pending -> Judging -> Result status.
11. Explain a failed submission.
12. Run AI code review.
13. Request level 1, 2, and 3 hints.
14. Open the training graph.
15. Review the submission trail.
16. Confirm hidden testcase details are not exposed.

## Known Limits

- The bundled frontend currently uses Monaco and Shiki directly, so production chunks are large.
- MLE classification depends on Docker runtime exit behavior.
- AI quality depends on the configured OpenAI-compatible model.
- The AI review UI is submission-oriented; reviewing unsaved code is implemented through the latest run/submission flow.
- The initial Alembic migration is a baseline for the current schema and should be validated against existing production databases before rollout.
