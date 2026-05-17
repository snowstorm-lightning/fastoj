# Codex Progress

## 2026-05-17 DeepSeek Authoring And Library Layout Follow-up

- [x] Diagnosed DeepSeek v4 `validation_failed` drafts as likely function-mode argument-shape brittleness plus overly terse admin validation messaging.
- [x] Added safe function-mode testcase argument normalization for generated drafts: JSON-lines, a single JSON argument array, and a single JSON object keyed by function parameter name are accepted.
- [x] Updated the dynamic Python function-mode submission wrapper to use the same argument normalization as draft validation, avoiding validation/runtime drift after draft approval.
- [x] Hardened authoring validation output so sandbox executor details are summarized as status/count metadata and secret-like testcase-derived stderr/output is not persisted in validation reports.
- [x] Tightened the problem-authoring prompt for function-mode return values and deterministic canonical ordering for combination/set-like outputs.
- [x] Added an admin validation summary UI so `validation_failed` drafts show failed checks, testcase counts, failed-case counts, and sandbox statuses instead of a raw JSON block.
- [x] Added a persisted problem-library card/list layout toggle; list mode renders an OJ-style one-row-per-problem view with difficulty, tags, supported modes, solved count, acceptance rate, and open action.
- [x] Full checks passed: `uv run ruff check .`, `uv run pytest` (92 passed), `cd frontend && npm run build`, and `cd frontend && npm test` (8 files / 13 tests passed).
- [x] Docker verification passed: `docker compose up --build -d api worker`, `docker compose ps`, and HTTP health at `http://127.0.0.1:8000/api/v1/health`.
- [x] Browser smoke passed for the real Docker-served problem library: card/list toggle works, list mode rendered 15 rows, card mode rendered 15 cards, both had no horizontal overflow, and visible text had no `[object Object]` or hidden-test sentinels. Screenshot capture still timed out in the browser plugin.

## 2026-05-17 Acceptance Harness And Product Polish

- [x] Ran dynamic Phase 1 discovery using the existing AGENTS/README/handoff/progress context and inspected the dirty worktree before edits.
- [x] Used specialist subagents for code mapping, product planning, frontend design planning, acceptance harness planning, and safety/privacy review; all subagents were closed after their outputs were integrated.
- [x] Performed browser visual/UX audit against the Docker-served app at `http://127.0.0.1:8000`.
- [x] Added frontend API error formatting helpers and tests so validation failures do not render `[object Object]` or stringify arbitrary structured payloads.
- [x] Sanitized AI problem-authoring schema errors so non-missing Pydantic validation failures report path/type summaries without raw draft values.
- [x] Added localized public problem search helpers and tests so Chinese seeded titles such as `两数之和` can match in the library without querying testcase content.
- [x] Cleared stale workbench AI/judge state on problem changes and new runs/submissions; stale WebSocket, polling, and AI callbacks are ignored by submission/problem id.
- [x] Fixed 1280px workbench horizontal overflow by constraining side panel grid tracks.
- [x] Added CSS design tokens for colors, radius, border depth, shadows, focus states, status colors, and restrained AI glow; applied them to core buttons, cards, panels, and workbench/admin shells.
- [x] Added `docs/ACCEPTANCE_HARNESS.md` as the repeatable baseline plus browser smoke matrix and automation roadmap without adding Playwright in this batch.
- [x] Updated README, Chinese README, progress, and handoff docs for the current behavior and verification.
- [ ] Convert the manual browser harness to Playwright or equivalent automated browser tests.

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
- [x] Added a trusted-shell admin bootstrap script so the first administrator can be created without opening public role assignment.
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
- [x] Recovery context consolidated into handoff/progress docs; obsolete standalone recovery prompt removed.
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
- [x] Removed obsolete static frontend prototype files and stale Codex checkpoint artifacts.
- [x] README updated with first-admin bootstrap and admin-account security notes.
- [ ] Final summary.

## Verification

- [x] `uv run ruff check .` passed after the 2026-05-17 acceptance/product polish batch.
- [x] `uv run pytest` passed after the 2026-05-17 batch, 87 tests passed with existing datetime deprecation warnings.
- [x] `cd frontend && npm run build` passed after the 2026-05-17 frontend edits, with existing Monaco/Shiki chunk-size warnings.
- [x] `cd frontend && npm test` passed after the 2026-05-17 frontend edits, 8 test files and 13 tests passed with expected jsdom canvas warnings.
- [x] `docker compose up --build -d api worker` passed after the 2026-05-17 batch.
- [x] `docker compose ps` reported API and worker healthy after the rebuild; PostgreSQL and Redis healthy; judge runtime running.
- [x] HTTP health passed at `http://127.0.0.1:8000/api/v1/health`.
- [x] Browser smoke covered rendered library/workbench pages at 1280px, localized Chinese UI, public run status, AI stale-state clearing, no `[object Object]`, and no visible hidden testcase content in the observed run result.
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
- [x] Local Qwen service deployed with `llama-server` b9060 outside the repo under a user-level `%USERPROFILE%\Models\qwen` directory; `/v1/models` and `/v1/chat/completions` passed smoke tests on `http://127.0.0.1:8080/v1`; reusable start/stop scripts were created in that external directory.
- [x] FastOJ Docker API verified `qwen-local` end to end: registered/logged in a temporary user, selected a public problem, and received an AI hint through `host.docker.internal:8080/v1` without printing AI response text.
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
- [x] Created handoff/progress files.
- [x] Removed obsolete checkpoint patch and recovery prompt after their useful context was consolidated into handoff/progress docs.
- [x] Created checkpoint commit `74f7c68 chore: checkpoint codex progress`.
- [x] Commit latest Docker/migration compatibility fixes.
- [x] Commit frontend training workspace simplification.
- [x] Commit documentation updates.
