# Codex Progress

## Phase 0: Dependency Audit

- [x] Checked repository dependency files and Docker files.
- [x] Checked local Python, uv, Node, npm, Docker, Docker Compose versions.
- [x] Ran `uv sync`.
- [x] Created frontend `package.json` and lockfile.
- [x] Enabled npm exact dependency versions.
- [x] Installed frontend runtime dependencies.
- [x] Installed frontend test/lint dependencies.
- [x] Created minimal Vite/Vitest scaffold.
- [x] Ran minimal frontend build.
- [x] Ran minimal frontend test.
- [x] Created `docs/dependency-audit.md`.

## Backend AI

- [x] Added AI config.
- [x] Added provider abstraction.
- [x] Added disabled provider.
- [x] Added OpenAI-compatible provider.
- [x] Added structured response schemas.
- [x] Added prompt modules.
- [x] Added AI service with hidden-test filtering.
- [x] Added AI API router.
- [x] Added tests for disabled provider, mock provider, hidden-test redaction, and ownership-sensitive paths.
- [ ] Validate OpenAPI output in a running browser session.

## Admin Problem Authoring Agent

- [x] Added `ProblemDraft`, `AgentRun`, and `AgentStep` models plus Alembic migration.
- [x] Added admin-only draft creation, run detail, draft list/detail, approve, and reject endpoints.
- [x] Added structured problem-authoring prompt and Pydantic validation for model JSON.
- [x] Added sandbox-backed validation adapter for ACM drafts and Python function-mode JSON-line drafts.
- [x] Approval creates formal `Problem`, `TestCase`, and official `Solution` rows only after admin action.
- [x] Added backend tests for admin-only access, AI disabled behavior, persistence, approval, idempotency, hidden cases, and validation failure.
- [x] Added minimal Admin Console UI for generating drafts, viewing run steps, previewing validation, approving, and rejecting.
- [x] Added dynamic Python function-mode metadata for approved Agent drafts, including workbench starter generation and submission wrapping.
- [ ] Add non-Python dynamic function-mode harness metadata for arbitrary approved function drafts.

## Judge Queue And Worker

- [x] Added Redis Streams enqueue.
- [x] Added consumer group creation.
- [x] Added ack helper.
- [x] Added retry/dead-letter helper.
- [x] Added pending reclaim helper.
- [x] Updated worker loop to read stream messages.
- [x] Added duplicate testcase result guard.
- [x] Added retry/dead-letter unit tests.
- [ ] Manually exercise dead-letter behavior with real Redis.

## WebSocket Status

- [x] Registered judge WebSocket router.
- [x] Added API-side Redis pub/sub relay.
- [x] Removed worker direct WebSocket manager calls.
- [x] Added worker status event publication.
- [x] Added WebSocket submission ownership check.
- [ ] Add WebSocket integration tests.
- [ ] Verify frontend WebSocket fallback behavior end to end in browser.

## Sandbox Security

- [x] Docker-first execution.
- [x] Unsafe local execution gated by env var.
- [x] Added Docker network disabled.
- [x] Added memory and memswap limits.
- [x] Added pids limit.
- [x] Added cap drop.
- [x] Added no-new-privileges.
- [x] Finish Docker source/stdin injection for worker-in-container execution.
- [x] Added non-root user.
- [x] Added output truncation.
- [x] Added CE/TLE/MLE/RE/SE mapping improvements.
- [x] Built Docker judge image successfully.
- [x] Added NumPy and CPU PyTorch to the Docker judge image.
- [x] Add sandbox hidden-output isolation test.
- [ ] Manually run representative judge submissions in browser.

## Frontend

- [x] Vite + React + TypeScript scaffold.
- [x] Tailwind/PostCSS config.
- [x] Zod schemas.
- [x] API client.
- [x] Zustand localStorage draft/cache store.
- [x] Pretext adapter.
- [x] Pretext adapter uses `prepareWithSegments`, `measureNaturalWidth`, `measureLineStats`, and `layoutWithLines`.
- [x] Problem library, focused workbench, and training graph split into separate views.
- [x] Workbench detail dock tabs for statement, public cases, solution, judge terminal, and submission trail.
- [x] AI Copilot dense details collapsed into expandable sections.
- [x] Core function-mode workbench with collapsible statement and result sidebars.
- [x] Smooth resizable statement/result sidebars with narrower collapsed state.
- [x] Dedicated login/register page instead of header-embedded auth fields.
- [x] Redirect unauthenticated run/submit attempts to the login page.
- [x] Show a localized token-expiry alert before redirecting to login when submit detects an expired session.
- [x] Added clearer hover titles to main workflow buttons.
- [x] Added 3D button states and compact three-bar collapsed sidebar controls.
- [x] Added single-button function/ACM mode toggle in the workbench.
- [x] Added frontend-side Chinese/English i18n for UI chrome, verdict labels, hover explanations, auth, tabs, problem display text, AI Copilot, and submission trail.
- [x] Added static visual step panels for supported problem types.
- [x] Fixed workbench outer viewport locking with internal panel scroll.
- [x] Added sample input/output/explanation rendering in the public cases panel.
- [x] Added frontend mode metadata and starter-template tests.
- [x] Monaco editor component.
- [x] AI Copilot panel.
- [x] xterm judge timeline.
- [x] Training graph with @xyflow/react.
- [x] Submission trail.
- [x] Wire Shiki code block rendering.
- [x] Run and fix full frontend build/test after app implementation.
- [x] Add frontend smoke tests for schemas, textLayout, graph, copilot.
- [x] Make graph node click drive actual tag filtering.

## Database And Migrations

- [x] Added Alembic env and script template.
- [x] Added initial baseline migration.
- [x] Avoided unconditional production `Base.metadata.create_all`; now only runs in debug.
- [x] Added migration stamp fallback for existing prototype DB volumes.
- [x] Validated API startup against existing PostgreSQL Docker volume.
- [x] Update README with migration workflow.

## Documentation

- [x] Dependency audit doc.
- [x] Checkpoint handoff doc.
- [x] Progress checklist doc.
- [x] Recovery prompt doc.
- [x] README full rewrite.
- [x] README updated for simplified frontend architecture and Pretext adapter usage.
- [x] README updated for function/ACM modes, AI algorithm seed problems, and latest verification.
- [x] README updated for dedicated auth page and resizable sidebars.
- [x] README updated for i18n, single mode-toggle, expanded interview-list/AI seed problems, and latest Docker verification.
- [x] README updated for DeepSeek/local AI configuration, API key storage, judge NumPy/PyTorch dependencies, and latest real-run verification.
- [x] README updated for token-expiry alert, AI response normalization, expanded testcase counts, Softmax verification, and latest 71-test backend result.
- [x] README/Chinese README updated for AI model selector, local Qwen profile status, structured sample cards, and acceptance-rate clamping.
- [x] AGENTS.md refreshed with current stack, commands, constraints, and documentation expectations.
- [x] Added account profile editing UI with close control, avatar preview, username/email/avatar/password fields, and persisted compact/display preferences.
- [x] Added admin-only backend router and frontend admin console for user role/active state and basic problem visibility/difficulty management.
- [x] AI explain/review/hint requests now carry active locale, and explain cache keys include locale to avoid English responses on Chinese pages.
- [x] Official solution endpoint can return Chinese explanations for seeded problems when `locale=zh`.
- [x] Added language-specific function starters for Python, C++, Java, JavaScript, TypeScript, Go, and selected C signatures.
- [x] Added custom hover tooltip styling for icon controls and reduced the knowledge-graph intro panel footprint.
- [x] Fixed Docker sandbox compiled-language execution so stdin is redirected to the final program instead of the compiler.
- [x] Fixed Docker sandbox workspace permissions so `nobody` can create compiled binaries inside `/tmp/work` without adding capabilities.
- [ ] Final summary.

## Verification

- [x] `uv sync`.
- [x] `uv sync --extra dev`.
- [x] `uv run ruff check .`.
- [x] `uv run pytest`.
- [x] Full frontend `npm run build`.
- [x] Full frontend `npm test`.
- [x] `docker compose up --build -d`.
- [x] API health check returned HTTP 200.
- [x] Docker API serves rebuilt frontend HTML at `http://localhost:8000`.
- [x] Function mode unit tests.
- [x] Frontend mode metadata tests.
- [x] Remove legacy prototype testcase compatibility; standardize function mode on JSON-line testcase input only.
- [x] Add interview-list seed problems and extra AI algorithm seed problems.
- [x] JSON-equivalent judge output comparison to avoid false WA on formatting.
- [x] Docker rebuild passed after auth/resizable sidebar work.
- [x] API health check returned HTTP 200 after latest rebuild.
- [x] Docker rebuild passed after latest sidebar button and WA compatibility fixes.
- [x] API and worker health checks reported healthy after latest rebuild.
- [x] `uv run pytest` passed after latest WIP, 68 tests passed with 3 datetime deprecation warnings.
- [x] `requests<2.32` lock update verified locally and in Docker build to restore Docker SDK socket access.
- [x] `uv run pytest` passed after model selector and acceptance-rate clamping, 71 tests passed with 3 datetime deprecation warnings.
- [x] `cd frontend && npm run build` passed after model selector, graph localization, discussion/settings, and sample-card UI.
- [x] `cd frontend && npm test` passed after model selector and graph test update, 6 test files and 8 tests passed.
- [x] `uv run pytest` passed after account/admin/AI-locale/function-starter edits, 72 tests passed with 3 datetime deprecation warnings.
- [x] `cd frontend && npm run build` passed after account/admin/AI-locale/function-starter edits, with existing Monaco/Shiki chunk-size warnings.
- [x] `cd frontend && npm test` passed after account/admin/AI-locale/function-starter edits, 6 test files and 8 tests passed.
- [x] `docker compose up --build -d api worker` passed after the latest sandbox/function-mode edits; API and worker are healthy.
- [x] HTTP health and rebuilt frontend checks passed at `http://127.0.0.1:8000`.
- [x] Real Docker-backed public run for Two Sum C++ function mode passed with `result=ac`.
- [x] `docker compose up --build -d api` passed; API container rebuilt with the latest frontend bundle.
- [x] `Get-Command llama-server` returned no installed command; local Qwen profile is wired but the actual local server is not started.
- [x] Real Docker-backed public run no longer fails for Two Sum function mode.
- [x] Final Docker health check passed after Docker Desktop restart on 2026-05-14.
- [x] Worker-in-container Docker SDK access verified with requests 2.31.0 and Docker ping returning `True`.
- [x] Fixed missing `/tmp/work/solution.py` and `/tmp/work/input.txt` by removing tmpfs from Docker archive injection.
- [x] Fixed async worker to execute task `judge_code` instead of raw stored user code.
- [x] Docker rebuild passed after i18n/single mode-toggle/problem-set work.
- [x] API health and rebuilt frontend HTTP checks passed after latest Docker rebuild.
- [x] Seed data was run in Docker and created 12 missing problems in the current database.
- [x] Seed data normalized existing local DB testcase rows to JSON-line input without deleting referenced testcase records.
- [x] Judge runtime import test passed for both NumPy and PyTorch.
- [x] Real API public run and full submit passed for function mode.
- [x] Real API public run and full submit passed for ACM mode.
- [x] Seed data now guarantees at least 10 testcase rows and at least two public samples for every bundled problem.
- [x] Real API public run passed for Softmax Cross Entropy.
- [x] DeepSeek-compatible AI hint/explain/review responses passed backend schema validation after scalar/list normalization.
- [x] `uv run ruff check .` passed after latest AI/parser/frontend/testcase edits.
- [x] `uv run pytest` passed after latest AI/parser/frontend/testcase edits, 71 tests passed with 3 datetime deprecation warnings.
- [x] `cd frontend && npm run build` passed after latest token-expiry alert and fixed-viewport workbench edits.
- [x] `cd frontend && npm test` passed after latest frontend edits, 6 test files and 8 tests passed.
- [x] `docker compose up --build -d api` passed and rebuilt/recreated API with the latest frontend bundle.
- [x] `docker compose ps` reports API and worker healthy; PostgreSQL and Redis healthy; judge runtime running.
- [x] HTTP health and rebuilt frontend checks passed at `http://127.0.0.1:8000`; `localhost` may time out in the current PowerShell session.
- [ ] Browser manual acceptance path.

## Checkpoint

- [x] Ran `git status`.
- [x] Ran `git diff --stat`.
- [x] Created handoff/progress/recovery files.
- [x] Generated `docs/codex-checkpoint.patch`.
- [x] Created checkpoint commit `74f7c68 chore: checkpoint codex progress`.
- [x] Commit latest Docker/migration compatibility fixes.
- [x] Commit frontend training workspace simplification.
- [x] Commit documentation updates.
