# Codex Handoff

Updated: 2026-05-13

## Current Goal

Upgrade the current FastAPI + PostgreSQL + Redis + Docker Worker + static frontend FastOJ prototype into an AI-explainable interview training OJ platform. The target includes AI explanation/review/hints, hidden-test isolation, Redis Streams worker flow, WebSocket-first judge status, Docker sandbox hardening, Vite + React + TypeScript frontend, tests, Docker verification, and README updates.

## Completed So Far

- Phase 0 dependency audit completed and recorded in `docs/dependency-audit.md`.
- Vite + React + TypeScript frontend implemented with Tailwind, Monaco, TanStack Query, Zustand, Zod, xterm, Shiki, @xyflow/react, and Pretext adapter.
- Frontend information architecture simplified into a problem library, focused workbench, and training graph.
- Workbench now keeps code editor and AI Copilot as the primary focus; statement, public cases, official solution, judge terminal, and submission trail are in a tabbed detail dock.
- AI Copilot details are collapsed behind expandable sections by default to reduce cognitive load.
- Pretext is wrapped by `frontend/src/lib/textLayout.ts` and used by problem cards, graph nodes, and submission trail summaries.
- Backend AI module implemented with disabled and OpenAI-compatible providers, structured explain/review/hint responses, JSON fallback wrapping, and hidden-test filtering.
- AI endpoints added under `/api/v1/ai`.
- Redis Streams judge queue implemented with consumer groups, ack, retry, dead-letter helpers, pending reclaim, and status pub/sub.
- Worker now consumes Redis Stream messages and publishes judge status through Redis instead of importing API WebSocket internals.
- API relays Redis judge status events to WebSocket clients.
- Submission detail and WebSocket status access are owner/admin aware.
- Sandbox execution is Docker-first with unsafe local execution gated by `FASTOJ_ALLOW_UNSAFE_LOCAL_EXECUTION=true`.
- Docker sandbox was hardened with disabled networking, memory/memswap limits, pids limit, cap drop, no-new-privileges, read-only root, tmpfs workspace, non-root execution, output truncation, and clearer verdict mapping.
- Alembic baseline added.
- Added `backend/scripts/migrate_or_stamp.py` so existing prototype databases with tables but no `alembic_version` are stamped safely before startup.
- README rewritten with architecture, AI provider, llama.cpp, migrations, testing, sandbox, WebSocket, and known limits.
- Checkpoint commit already exists: `74f7c68 chore: checkpoint codex progress`.
- Docker Compose startup fix commit exists: `e00a30c fix: make docker compose startup robust`.
- Frontend simplification commit exists: `b36053b refactor: simplify frontend training workspace`.
- Docker Compose now builds and starts successfully after Dockerfile fixes.

## Not Completed Yet

- Full browser manual acceptance path has not been executed by Codex.
- WebSocket fallback behavior has not been verified in a real browser session.
- Real Redis dead-letter behavior is covered by unit-level tests but not manually exercised end to end.
- Frontend bundle size is large because Monaco and Shiki are loaded directly.

## Current Modified File List

No modified or untracked files at the time of this handoff update, before the documentation-only commit requested by the user.

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

## Next Minimal Continue Plan

1. Run the browser manual acceptance path at `http://localhost:8000`.
2. Exercise a real submit/run flow and verify WebSocket status before polling fallback.
3. If production data already exists, review the baseline migration/stamp strategy before rollout.
4. Optionally split Monaco/Shiki into lazy chunks to reduce initial frontend bundle size.
