# Codex Handoff

Updated: 2026-05-13

## Current Goal

Upgrade the current FastAPI + PostgreSQL + Redis + Docker Worker + static frontend FastOJ prototype into an AI-explainable interview training OJ platform. The target includes AI explanation/review/hints, hidden-test isolation, Redis Streams worker flow, WebSocket-first judge status, Docker sandbox hardening, Vite + React + TypeScript frontend, tests, Docker verification, and README updates.

## Completed So Far

- Phase 0 dependency audit completed.
- Verified local toolchain:
  - Python 3.12.10
  - uv 0.10.2
  - Node.js v24.15.0
  - npm 11.12.1
  - Docker 29.2.1
  - Docker Compose v5.1.0
- `uv sync` passed after approved access to the user-level uv cache.
- Created Vite + React + TypeScript frontend scaffold.
- Enabled npm exact versions with `npm config set save-exact true`.
- Installed required frontend runtime and test dependencies.
- Frontend minimal `npm run build` passed.
- Frontend minimal `npm test` passed.
- Created `docs/dependency-audit.md`.
- Added backend AI module skeleton:
  - OpenAI-compatible provider
  - disabled provider
  - structured schemas
  - explain/review/hint prompts
  - AI service with JSON repair/fallback and hidden-test filtering
- Added AI API router:
  - `POST /api/v1/ai/submissions/{submission_id}/explain`
  - `POST /api/v1/ai/submissions/{submission_id}/review`
  - `POST /api/v1/ai/problems/{problem_id}/hint`
- Added AI and queue/sandbox settings to `backend/core/config.py`.
- Started Redis Streams queue conversion:
  - stream enqueue
  - consumer group
  - ack
  - retry/dead-letter
  - pending reclaim helper
  - judge status pub/sub
- Updated worker to consume Redis Stream messages.
- Removed direct worker-to-API WebSocket manager usage in the worker path.
- Added API-side Redis pub/sub status relay to WebSocket clients.
- Registered WebSocket judge router in `backend/main.py`.
- Added submission ownership checks for WebSocket status.
- Added admin-aware submission detail access.
- Added language validation including `typescript`.
- Hardened sandbox path:
  - Docker-first behavior
  - unsafe local execution gated by `FASTOJ_ALLOW_UNSAFE_LOCAL_EXECUTION`
  - network disabled
  - memory and memswap limits
  - pids limit
  - cap drop
  - no-new-privileges
  - read-only root filesystem
  - tmpfs work dirs
  - non-root user
  - output truncation
  - CE/TLE/MLE/RE/SE mapping improvements
- Added Alembic baseline files.
- Started React frontend implementation:
  - Zod schemas
  - API client
  - localStorage draft/cache store
  - Pretext adapter
  - Monaco code editor component
  - AI Copilot panel
  - xterm judge timeline
  - submission trail
  - @xyflow/react training graph
  - first full app shell in `frontend/src/main.tsx`

## Not Completed Yet

- `docker compose up --build -d` could not be completed because Docker Desktop Linux daemon was not running in this environment.
- Full browser manual acceptance was not executed because Docker services could not be started.
- Alembic baseline should still be reviewed before use against an existing production database.
- Frontend bundle size is large because Monaco and Shiki are loaded directly.
- Frontend graph tag click currently records intent but does not fully drive shared problem-console filters.

## Current Modified File List

Tracked modified files from `git status --short`:

- `backend/api/submissions/__init__.py`
- `backend/api/submissions/run.py`
- `backend/api/websocket/judge.py`
- `backend/api/websocket/manager.py`
- `backend/core/config.py`
- `backend/core/languages.py`
- `backend/main.py`
- `backend/sandbox/executor.py`
- `backend/services/queue_service.py`
- `backend/services/submission_service.py`
- `backend/worker/judge_worker.py`
- `backend/worker/tasks/consumer.py`
- `backend/worker/tasks/judge_task.py`

New/untracked paths currently present:

- `backend/ai/`
- `backend/alembic/`
- `backend/api/ai.py`
- `backend/api/websocket/status_relay.py`
- `docs/`
- `frontend/eslint.config.js`
- `frontend/index.html`
- `frontend/node_modules/`
- `frontend/package-lock.json`
- `frontend/package.json`
- `frontend/postcss.config.js`
- `frontend/src/components/`
- `frontend/src/main.tsx`
- `frontend/src/smoke.test.tsx`
- `frontend/src/stores/`
- `frontend/src/styles.css`
- `frontend/tailwind.config.js`
- `frontend/tsconfig.json`
- `frontend/tsconfig.node.json`
- `frontend/tsconfig.node.tsbuildinfo`
- `frontend/tsconfig.tsbuildinfo`
- `frontend/vite.config.d.ts`
- `frontend/vite.config.js`
- `frontend/vite.config.ts`
- `tests/test_ai_service.py`
- `tests/test_auth_api.py`
- `tests/test_judge_task_security.py`
- `tests/test_queue_streams.py`

## Executed Commands And Results

- `python --version`: passed, Python 3.12.10.
- `uv --version`: passed, uv 0.10.2.
- `node --version`: passed, v24.15.0.
- `npm --version`: passed, 11.12.1.
- `docker --version`: passed, Docker 29.2.1.
- `docker compose version`: passed, Docker Compose v5.1.0.
- `uv sync`: initially failed in sandbox due uv cache permissions; passed after approved rerun.
- `npm config set save-exact true`: initially failed in sandbox due user `.npmrc` permissions; passed after approved rerun.
- `npm install react react-dom @vitejs/plugin-react vite typescript tailwindcss postcss autoprefixer monaco-editor @tanstack/react-query zustand zod @xterm/xterm @xterm/addon-fit shiki @xyflow/react @chenglou/pretext`: initially failed in sandbox due npm registry cache-only mode; passed after approved network rerun.
- `npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom eslint @eslint/js typescript-eslint eslint-plugin-react-hooks`: passed.
- `npm install -D @types/node @types/react @types/react-dom`: passed.
- `npm install -D @tailwindcss/postcss`: passed.
- `npm run build`: passed for Phase 0 minimal scaffold after Tailwind 4 PostCSS fix and approved Vite process spawn.
- `npm test`: passed for Phase 0 minimal smoke test after approved Vite/Vitest process spawn.
- `git status --short`: passed, showed WIP tracked and untracked files.
- `git diff --stat`: passed, tracked diff stat currently 13 files changed, 372 insertions, 92 deletions. Untracked files are not included in that stat.
- `git diff --name-only`: passed, listed tracked modified files.
- `uv sync`: passed in final verification.
- `uv sync --extra dev`: passed in final verification.
- `uv run ruff check .`: passed.
- `uv run pytest`: passed, 60 tests passed with 3 datetime deprecation warnings.
- `cd frontend && npm run build`: passed, with expected large chunk warnings from Monaco/Shiki.
- `cd frontend && npm test`: passed, 5 tests passed; jsdom printed canvas `getContext` not implemented warnings.
- `docker compose config`: passed.
- `docker compose up --build -d`: failed because Docker Desktop Linux daemon was not running.

## Failed Commands And Error Summary

- `uv sync` failed first with `Failed to initialize cache at C:\Users\Lightning\AppData\Local\uv\cache`, `os error 5`, permission denied opening `.git` in uv cache. Rerun with approved `uv sync` permission passed.
- `npm config set save-exact true` failed first with `EPERM: operation not permitted, open C:\Users\Lightning\.npmrc`. Rerun with approved `npm config set` permission passed.
- First frontend dependency install failed with `ENOTCACHED`, registry request unavailable in sandbox cache-only mode. Rerun with approved `npm install` network permission passed.
- Initial `npm run build` failed due TypeScript 6 deprecation for `moduleResolution: Node`; fixed by switching to `Bundler`.
- Next `npm run build` failed due missing Node/React type declarations and wrong Vite/Vitest config import; fixed by adding types and importing `defineConfig` from `vitest/config`.
- Vite/Vitest sandbox runs failed with `spawn EPERM`; approved reruns passed.
- Build failed once with Tailwind 4 PostCSS plugin error; fixed by installing `@tailwindcss/postcss` and updating `postcss.config.js`.
- Docker Compose startup failed with `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`; this indicates Docker Desktop Linux engine was not running.

## Next Minimal Continue Plan

1. Start Docker Desktop Linux engine.
2. Re-run `docker compose up --build -d`.
3. Execute the browser manual acceptance path from `README.md`.
4. Review the Alembic baseline against any existing persistent database before production rollout.
