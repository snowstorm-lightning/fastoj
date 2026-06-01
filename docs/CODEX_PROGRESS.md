# Codex Progress

## 2026-06-01 CI/CD And Tencent Cloud Deployment Prep

- [x] Added GitHub Actions CI for backend lint/tests and frontend build/tests on PRs and `master` pushes.
- [x] Added a self-contained deploy workflow that runs the same quality gate, builds API/worker/judge images on GitHub Actions, pushes them to GHCR, SSHes as `ubuntu`, uploads the production Compose file, pulls images, and restarts services on Tencent Cloud.
- [x] Added `docker-compose.prod.yml` for server-side image-based deployment without source bind mounts.
- [x] Kept `.env` as the only runtime environment filename for both local and server use; added `.env.prod.example` for `/opt/projects/fastoj/.env` and documented that `.env.dev` is optional and unnecessary for the normal local-plus-server flow.
- [x] Updated local Compose to expose PostgreSQL, Redis, and API ports through `.env` variables while retaining loopback defaults.
- [x] Added Chinese deployment documentation in `docs/DEPLOYMENT.md` and linked it from both READMEs.
- [x] Docker Compose config validation passed for local `.env.example` and production `.env.prod.example`; production Compose was tightened to avoid passing unrelated `.env` keys into containers.

## 2026-05-29 Account-Backed Locale Preference

- [x] Added a persisted `users.locale` profile field with an Alembic migration and `/auth/me` response/update support.
- [x] Updated registration to save the active UI language and made the header/settings language switch sync to the signed-in account while still supporting guest local storage.
- [x] Added frontend locale helpers for normalization, browser-language fallback, storage writes, and `<html lang>` updates.
- [x] Made AI-related frontend API methods require an explicit `Locale` argument so new calls do not silently default to English.
- [x] Cleared stale AI copilot state on UI language changes and improved tag query normalization for Chinese commas and case variants.
- [x] Verification passed: `uv run ruff check .`; `uv run pytest` (141 passed); `cd frontend && npm run build`; `cd frontend && npm test` (9 files / 25 tests passed).

## 2026-05-29 Multi-Language Authoring Draft Solutions

- [x] Added `target_languages` to admin Problem Authoring Agent requests while keeping the legacy `target_language` field compatible.
- [x] Added multi-language `official_solutions` draft schema/API support, persisted draft solution lists, and an Alembic migration for `problem_drafts.official_solutions_json`.
- [x] Updated draft validation to require requested solution languages and sandbox-check every official solution language before approval.
- [x] Updated draft approval to publish one official `Solution` row per generated/edited language.
- [x] Updated the admin authoring UI with target-language checkboxes, per-language official solution editors, and per-language testcase validation chips.
- [x] Updated README and Chinese README for multi-language authoring behavior.
- [x] Verification passed: `uv run ruff check .`; `uv run pytest` (137 passed); `cd frontend && npm run build`; `cd frontend && npm test` (9 files / 23 tests passed).

## 2026-05-29 Dynamic AI Profile Availability

- [x] Planned and implemented dynamic AI profile discovery for `default`, `deepseek`, and `qwen-local` through `GET /api/v1/ai/profiles`.
- [x] Added background profile health checks with short timeouts, 60-second cache, configuration preflight, `/models` probing, and chat-completions fallback.
- [x] Changed `default` AI routing to choose the first healthy profile from default config, DeepSeek, then local Qwen; unavailable providers still return normal 503 errors at call time.
- [x] Updated the workbench and admin authoring UI to use backend-provided profile availability instead of hard-coded model options.
- [x] Regular users only see available model options; admins can see unavailable authoring profiles and safe failure reasons.
- [x] Verification passed: `uv run ruff check .`, `uv run pytest` (127 passed), `cd frontend && npm run build`, `cd frontend && npm test` (9 files / 22 tests passed), `docker compose up --build -d api`, `docker compose ps api` healthy, and API health at `http://127.0.0.1:8010/api/v1/health`.

## 2026-05-29 Admin Authoring And Testcase Management

- [x] Added bounded Problem Authoring Agent repair: a failed draft validation now feeds a safe repair context back to the model for at most two additional attempts before the final draft is persisted.
- [x] Repair context includes failed checks, public sample diagnostics, and aggregate case summaries only; hidden testcase input/output stays out of repair prompts, run output, and validation reports.
- [x] Added admin-only testcase CRUD endpoints for formal problems: list, create, update, and delete, including hidden/sample flags, score, and order.
- [x] Added admin UI testcase details for generated drafts and a formal-problem testcase manager with view/edit/create/delete controls.
- [x] Added admin-only published problem deletion with related testcase, solution, submission, and testcase-result cleanup.
- [x] Kept published-problem deletion inside the edit panel only, removing the row/card delete action to reduce accidental deletes.
- [x] Added explicit draft save-and-revalidate controls so admins can edit failed AI drafts and run validation again before approval.
- [x] Persisted draft target languages and made manual draft revalidation enforce that every selected language has a non-empty official solution and explanation.
- [x] Added admin AI fill for one missing draft official-solution language at a time; the prompt uses current draft fields, public samples, and existing solutions while omitting hidden testcase content.
- [x] Added grouped draft run history in admin responses/UI so generation, repair, manual edit, approval, and rejection events remain visible instead of being overwritten by the latest manual edit.
- [x] Added authoring `both` mode so the Agent request and draft editor can represent problems that support both function and ACM practice.
- [x] Switched `both` mode to a single canonical function-style official solution per language; validation wraps that function solution and ACM practice shares the same JSON-argument input/output contract.
- [x] Expanded the formal problem editor to cover slug, mode, function signature, ACM input/output formats, time/memory limits, multilingual official solutions, per-language AI fill, and save-and-revalidate.
- [x] Added admin official-solution CRUD and formal-problem revalidation endpoints; revalidation uses safe validation reports and does not expose hidden case content outside admin-only data.
- [x] Enforced hidden/sample testcase mutual exclusion on backend create/update and mirrored that constraint in the admin UI.
- [x] Hardened auth/submission boundaries so disabled-user tokens and judge WebSocket connections are rejected, and regular users cannot run or submit private problems directly.
- [x] Changed manual draft slug edits to ignore failed/rejected/historical approved drafts, reject true duplicate active slugs with a visible error, and stop silently appending a numeric suffix.
- [x] Hardened draft action buttons: approving now requires no unsaved edits and asks for confirmation; rejecting asks for confirmation; cancel is enabled only when there are local edits.
- [x] Made rejected drafts visually distinct in the draft list and added a cancel action for the formal-problem edit panel.
- [x] Relaxed authoring testcase-count validation to require at least one public testcase and one total testcase; hidden cases are recommended but no longer forced for simple drafts.
- [x] Fixed authoring validation for function solutions that return strings where expected output is represented as a JSON string literal.
- [x] Updated Docker Compose so the API service can use the Docker judge runtime for synchronous admin draft validation.
- [x] Updated README and Chinese README for the new admin testcase and authoring-agent behavior.
- [x] Verification passed: `uv run ruff check .`, `uv run pytest` (149 passed), `cd frontend && npm run build`, `cd frontend && npm test` (9 files / 25 tests passed), `docker compose up --build -d api`, `docker compose ps api` healthy, and API health at `http://127.0.0.1:8010/api/v1/health`.

## 2026-05-29 Workbench Run Panel And Auth Feedback

- [x] Added a LeetCode-style run result panel below the editor with editable public inputs, official-solution generated expected output, actual output, and red-highlighted diff lines for mismatches.
- [x] Added judge-worker heartbeat detection so async submissions fall back to inline Docker judging when Redis is up but no worker is alive, preventing runs from staying pending forever.
- [x] Made the frontend polling fallback append a final result/error event when WebSocket terminal events are missed.
- [x] Changed public-run custom cases so clients submit only input; the judge ignores client-provided expected output and generates it server-side from an official/reference solution, with public-sample fallback only for already visible samples.
- [x] Added backend support for public-only custom run cases while keeping hidden testcase inputs, expected outputs, actual outputs, and hidden progress metadata out of API/WebSocket responses.
- [x] Added registration confirm-password validation, clearer auth error dialogs, and a registration-success dialog before entering the problem library.
- [x] Moved visual problem guidance and official hints after public sample cards so they do not interrupt sample input/output reading.
- [x] Added an adjustable editor/result height splitter, increased the default editor height, widened left/right resize hit areas, and made side panels snap closed on pointer release near the edge.
- [x] Removed the duplicated AI Copilot public-case comparison block and made the right AI container flow with expanded detail content.
- [x] Fixed custom runs for Majority Element by adding a sandboxed reference generator, and made official function-solution wrapping use the function-signature fallback.
- [x] Fixed stale ACM starter drafts appearing in Python function mode; function mode now restores the function starter when an ACM template was cached under the function draft key.
- [x] Updated English and Chinese README page descriptions for the current auth and workbench behavior. Screenshot PNG regeneration was attempted but blocked by the current WSL/browser environment.
- [x] Verification passed for the touched surface: `uv run ruff check .` passed, `uv run pytest` (135 passed), frontend build passed, frontend tests passed (9 files / 23 tests), Docker API/worker rebuild and health passed, a real `print-qiu-qiu` run returned `ac`, and a real Majority Element custom-run smoke returned `ac` with generated expected output.

## 2026-05-26 Linux/WSL Deployment Pass

- [x] Verified current WSL toolchain: Docker Desktop Linux engine 29.2.1, Docker Compose v5.1.0, `uv 0.10.10`, Node v24.13.1, and npm 11.14.1.
- [x] Made Compose Linux-friendly by allowing `.env` overrides for PostgreSQL credentials and `SECRET_KEY`, and by mapping `host.docker.internal` to Docker `host-gateway` for native Linux local-AI access.
- [x] Updated `.env.example` for host-direct backend development against the Compose-published PostgreSQL port `5433`, Redis on `6379`, safe local secrets, and JSON syntax for list env vars.
- [x] Removed the obsolete `Dockerfile.dev` build-time `.env` copy and made it launch through `uv run`.
- [x] Aligned Python runner commands with Linux expectations by using `python3` on non-Windows hosts and in Docker judge execution paths.
- [x] Added frontend Node/npm engine metadata and refreshed the lockfile root metadata.
- [x] Updated English and Chinese README deployment guidance for Linux/WSL prerequisites, `npm ci`, direct backend `.env` settings, judge runtime build, `host.docker.internal` behavior, and Linux/WSL local Qwen commands.
- [x] Verification passed in WSL/Linux: `uv run ruff check .`, `uv run pytest` (96 passed), `cd frontend && npm run build`, `cd frontend && npm test` (8 files / 15 tests passed), `docker compose up --build -d api worker`, `docker compose ps` healthy, API health at `http://127.0.0.1:8000/api/v1/health`, frontend HTML served by the API container, worker-to-Docker judge smoke returned `ac`, and Docker seed script normalized 106 problems.

## 2026-05-18 Hot 100 Seed Catalog Expansion

- [x] Expanded the bundled seed catalog to 106 problems: all 100 canonical Hot 100 practice problems plus the existing 6 AI/ML algorithm exercises.
- [x] Added `backend/scripts/hot100_data.py` with original FastOJ statements, deterministic ACM input/output conventions for linked-list/tree/design/multi-answer tasks, and at least 3 base cases per new problem.
- [x] Kept existing function-mode classics and migrated the legacy `longest-substring-without-repeating` seed slug to canonical `longest-substring-without-repeating-characters` with backend/frontend compatibility aliases.
- [x] Added seed catalog regression tests for Hot 100 coverage, uniqueness, and canonical slug use.
- [x] Docker seed verification passed: `docker compose exec -T api uv run python -m backend.scripts.seed_data` created 91 missing problems and normalized 15 existing problems; database count verified at 106 problems and 1060 testcase rows.
- [x] Full checks passed: `uv run ruff check .`, `uv run pytest` (96 passed), `cd frontend && npm run build`, `cd frontend && npm test` (8 files / 15 tests passed), and HTTP health at `http://127.0.0.1:8000/api/v1/health`.

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
