# fastoj Development Guidelines

Last updated: 2026-06-13

## Current Stack

- Backend: Python 3.11+ as declared in `pyproject.toml`, FastAPI, SQLAlchemy 2.0, Pydantic v2, Redis Streams, PostgreSQL 14+.
- Judge: Docker-based sandbox execution via the Python Docker SDK. Production code must not fall back to host `subprocess`.
- Frontend: React + TypeScript + Vite, TanStack Query, Zustand, Monaco editor, React Flow.
- Tooling: `uv`, `ruff`, `pytest`, `npm`, Docker Compose.
- AI providers: DeepSeek-compatible API profile and a local Qwen profile. API keys stay in `.env`; never commit real secrets.

## Project Layout

```text
backend/
├── ai/           # AI provider configuration, prompts, response schemas
├── api/          # FastAPI route modules
├── core/         # Settings, database, security, logging
├── models/       # SQLAlchemy models
├── schemas/      # Pydantic API schemas
├── scripts/      # Seed/admin utilities
├── services/     # Business logic, judging helpers, function mode wrappers
└── worker/       # Judge worker
frontend/
├── src/
│   ├── components/
│   ├── lib/
│   ├── stores/
│   └── main.tsx
tests/            # Backend tests
docs/             # Codex handoff/progress/recovery notes
```

## Required Commands

Run these before handing off substantial changes:

```bash
uv run ruff check .
uv run pytest
cd frontend && npm run build
cd frontend && npm test
```

When Docker behavior changes and a rebuild is genuinely required, also run:

```bash
docker compose up --build -d api
```

Do not use `--build` for routine startup, UI review, or "start the service" requests.
Reuse the existing environment first.

For ad hoc Python commands, one-off scripts, and local verification snippets, default to:

```bash
uv run python
```

Do not probe or rely on bare `python` first unless the task is specifically about interpreter discovery or PATH debugging.

## Local Runtime Rules

- PostgreSQL, Redis, and related backing services are Docker-managed in this project. Do not start or depend on host PostgreSQL/Redis for local FastOJ runtime unless the user explicitly asks for that mode.
- Before starting services, inspect current state with `docker compose ps` and listening ports. Reuse running containers and existing images.
- For routine startup or UI inspection, use non-building commands such as `docker compose up -d postgres redis api` and `cd frontend && npm run dev`; do not run `docker compose up --build`, `docker compose build`, `npm install`, or other dependency/image download commands unless required by a missing environment or explicitly approved by the user.
- If an image/container/dependency is missing and a build or download would be needed, stop and explain the situation before starting the expensive command.
- Vite is already configured to proxy `/api` and `/ws` to the Compose API on `127.0.0.1:8010`; prefer that path for browser review.

## Product Constraints

- Do not leak hidden test cases in UI, logs, docs, or AI prompts.
- AI prompts may include public samples and aggregate verdict details only; never include hidden case content.
- Keep public-sample behavior aligned with the current FastOJ product. Remove incompatible legacy public-input assumptions instead of preserving old behavior.
- Function mode and ACM mode are both first-class. Function mode should provide a clear starter frame; ACM mode should provide stdin/stdout starter code.
- The UI supports Chinese and English. Avoid mixed-language screens; AI output should follow the active page locale.
- Admin-only features must be gated by server-side role checks as well as frontend navigation.

## Dependency Rules

- Do not add dependencies without confirming they are needed and updating lock/config files.
- Numpy and PyTorch are allowed judge/runtime dependencies for AI algorithm exercises.
- Local Qwen support is configured as an HTTP provider profile; installing or running `llama-server`/model files may require user action.

## Code Style

- Prefer existing service and schema patterns over new abstractions.
- Keep edits scoped to the requested workflow.
- Use `rg` for search.
- Use `apply_patch` for manual file edits.
- Do not revert unrelated user changes in a dirty worktree.

## Documentation

- Keep `README.md`, `README.zh-CN.md`, `docs/CODEX_PROGRESS.md`, and `docs/CODEX_HANDOFF.md` current after behavior changes.
- Final handoffs should summarize test results and any known blockers.
