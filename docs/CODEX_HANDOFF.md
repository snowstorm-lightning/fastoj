# Codex Handoff

Updated: 2026-06-07

## Current Goal

Upgrade the current FastAPI + PostgreSQL + Redis + Docker Worker + static frontend FastOJ prototype into an AI-explainable interview training OJ platform. The target includes AI explanation/review/hints, hidden-test isolation, Redis Streams worker flow, WebSocket-first judge status, Docker sandbox hardening, Vite + React + TypeScript frontend, tests, Docker verification, and README updates.

## 2026-06-08 User Management And Account Recovery

- Added Alembic revision `20260608_0011` with `users.token_version`. Login and refresh tokens now include the version; password changes reject older access/refresh tokens. Legacy tokens without the version continue to work only while the user's stored version is still `0`.
- Added admin-only `POST /api/v1/admin/users/{user_id}/reset-password` for temporary password resets. The route hashes the new password, increments `token_version`, rejects self-reset, and is limited to highest administrators.
- `PATCH /api/v1/admin/users/{id}` now has stronger server-side safety: content admins with `user:manage` can only toggle ordinary users; role/permission edits and elevated-account operations require highest admin. Highest admins cannot disable/downgrade themselves or remove the last active admin.
- The frontend “Users & Permissions” page is now a focused account-management surface: rows show account/email, role chip, status chip, update time, and explicit action labels; role/permission editing and password reset live in the selected user's detail panel.
- Login now tells users who forgot passwords to contact an administrator. No email recovery table/SMTP flow was added in this pass.
- Verification passed: `uv run ruff check .`; `uv run pytest` (236 passed, 2 existing FastAPI `regex` warnings); `cd frontend && npm test` (10 files / 44 tests); `cd frontend && npm run build` (existing large chunk warnings).
- Runtime refresh passed: `docker compose up --build -d api`, `docker compose exec -T api uv run alembic -c backend/alembic.ini upgrade head`, and health check at `http://127.0.0.1:8010/api/v1/health`; API container reports healthy.

## 2026-06-07 Two-Car Parking Lot Seed Problem

- Added `Two-Car Parking Lot` as seed slug `two-car-parking-lot`; the bundled catalog is now 108 problems: 100 canonical Hot 100 entries, 6 AI/ML exercises, and 2 extra interview graph/search problems.
- The function signature is `def can_reach(grid: list[list[str]]) -> bool`. The official Python solution runs BFS over the combined state of both car positions, moving one car at a time while enforcing walls, bounds, and non-overlap.
- Seed cases include reachable grids, blocked parking spots, an impossible one-row passing case, a bypass case, and special hidden grids for the augmentation registry.

## 2026-06-07 Admin DeepSeek Pro Profile And Repair Budget

- Recent failed problem imports were model/schema failures, not judge failures. The latest failed `problem_import` runs ended with `AI provider returned JSON without a problem draft object`, and the model steps returned short or empty payloads before validation failed.
- The running container had both `default` and `deepseek` resolving to `deepseek-v4-flash` with `AI_MAX_OUTPUT_TOKENS=1200`. For full problem import/draft JSON, model strength and output budget are the immediate bottlenecks; the current 30000-character raw-material limit is far below 1M context.
- Added admin-only profile `deepseek-pro`, configured through `AI_DEEPSEEK_PRO_BASE_URL`, `AI_DEEPSEEK_PRO_API_KEY`, `AI_DEEPSEEK_PRO_MODEL=deepseek-v4-pro`, `AI_DEEPSEEK_PRO_TIMEOUT_SECONDS=120`, and `AI_DEEPSEEK_PRO_MAX_OUTPUT_TOKENS=4000`.
- The implementation uses the normal OpenAI-compatible DeepSeek model id `deepseek-v4-pro` without `[1m]`; `[1m]` is only for the Anthropic/Claude Code compatibility naming path.
- Regular user AI controls do not receive `deepseek-pro`, and non-admin AI actions passing that profile are rejected with 403. The admin Problem Agent defaults to `deepseek-pro` when available and still allows selecting other profiles.
- Authoring repair attempts are now configurable through `AI_AUTHORING_REPAIR_ATTEMPTS`, defaulting to 4 repair attempts plus the initial generation attempt. Runtime clamping keeps it between 0 and 8 repair attempts; do not make it unlimited because each attempt is a full model call.
- Verification passed: `uv run ruff check .`; `uv run pytest` (200 passed, existing FastAPI `regex` warnings); `cd frontend && npm test` (10 files / 38 tests); `cd frontend && npm run build` (existing large chunk warnings); `docker compose up --build -d api`; health check at `http://127.0.0.1:8010/api/v1/health`.
- Container config check confirmed: `default/deepseek -> deepseek-v4-flash`, `deepseek-pro -> deepseek-v4-pro`, Pro timeout 120s, Pro max output 4000, authoring repair attempts 4.

## 2026-06-07 Admin Agent Runs Trace Viewer

- Admins can now inspect recent Agent executions through `GET /api/v1/admin/agent/runs`, including failed `problem_import` runs that have no `draft_id`.
- Agent draft generation, problem import, and draft solution generation now wrap model/validation failures that already created a run as structured details: `{ message, run_id }`. The frontend keeps the message and automatically fetches the referenced run.
- The admin Problem Agent middle panel is now a summary-first trace viewer: recent runs are listed with type/status/model/draft linkage, the selected run shows a step timeline, and each step expands on click to show sanitized input/output/error JSON.
- The UI sanitizes trace detail display by redacting long/raw/code-like keys such as `raw_material`, `code`, `official_solution_code`, and hidden testcase collections, and truncates nested/long values so the page stays readable.
- Verification passed: `uv run ruff check .`; `uv run pytest` (196 passed, existing FastAPI `regex` warnings); `cd frontend && npm test` (10 files / 38 tests); `cd frontend && npm run build` (existing large chunk warnings); `docker compose up --build -d api`; health check at `http://127.0.0.1:8010/api/v1/health`.

## 2026-06-07 Seed Explanations Localization

- All 107 seed slugs now have bilingual sample and official-solution explanation text in `backend/scripts/seed_explanations.py`.
- Problem detail responses accept `locale` and include `sample_testcases[].explanation` for seed problems. Non-seed problems leave that field `null` so the frontend does not invent a sample explanation.
- Seed official solutions now store real English approach notes from the registry. `/solutions` returns localized seed explanations by request locale and still falls back to Python when the requested language is missing.
- The frontend workbench removed its hard-coded `sampleExplanation` fallback and no-solution pseudo-solution paragraph; it displays API-provided explanations only.
- The current API container database was reseeded successfully: `created 0 missing problems and normalized 107 existing problems`.
- Verification passed: `uv run ruff check .`; `uv run pytest` (194 passed, existing FastAPI `regex` warnings); `cd frontend && npm test` (10 files / 36 tests); `cd frontend && npm run build` (existing large chunk warnings).

## 2026-06-07 Seed Official Solutions And Hidden Case Expansion

- The bundled 107-problem seed catalog now has Python official solutions for every slug through `backend/scripts/seed_official_solutions.py`. `seed_data.py` uses this registry for seeded `Solution` rows, so placeholder/TODO official solutions are replaced during seed normalization.
- Seed testcase expansion now lives in `backend/scripts/seed_testcase_augmentation.py`. It deterministically builds at least two public cases per problem and enforces hidden-count lower bounds by problem type: ordinary problems 30+, design and AI/ML 20+, high-output combination problems 15+.
- Official seed solutions are pure function-mode implementations with signatures aligned to `FUNCTION_SIGNATURES`; the seed-wide harness executes them through `wrap_function_submission` and the same output matcher used by judging tests.
- Public `/solutions` now falls back to Python when a requested language has no official solution, while still returning the actual solution language as `python`. Existing requested-language solutions continue to win.
- Added backend regression coverage for full seed solution/case policy and API fallback, plus frontend API coverage for rendering a Python fallback solution.
- Verification passed: `uv run ruff check .`; `uv run pytest` (190 passed, existing FastAPI `regex` warnings); `cd frontend && npm test` (10 files / 34 tests); `cd frontend && npm run build` (existing large chunk warnings).

## 2026-06-07 Alien Dictionary Seed Problem

- Added `Alien Dictionary` as seed slug `alien-dictionary`; the bundled catalog is now 107 problems: 100 canonical Hot 100 entries, 6 AI/ML exercises, and this additional graph/topological-sort interview problem.
- The function signature is `def alienOrder(words: list[str]) -> str`, matching the LeetCode-style method name while fitting FastOJ function mode. A regression test verifies `class Solution.alienOrder(...)` submissions are wrapped and executed correctly.
- Seed cases cover the canonical valid-order sample, a two-letter order, cycle contradiction, invalid prefix ordering, and deterministic chain cases. The official Python solution uses Kahn topological sort and returns an empty string on prefix conflicts or cycles.
- Added English and Chinese statement-detail enrichment, Chinese title/hint localization, a Chinese official-solution explanation, frontend starter metadata, and a small topological-sort visual flow.
- Verification passed: `uv run ruff check .`; `uv run pytest` (184 passed, existing FastAPI `regex` warnings); `cd frontend && npm test` (10 files / 33 tests); `cd frontend && npm run build` (existing large chunk warnings).

## 2026-06-06 Problem Import Agent

- Admin now has a separate `导入题目` tab beside original authoring. It accepts an optional source URL, pasted raw material up to 30000 characters, adaptation notes, difficulty/tags/mode/model, and target-language selections.
- Backend API `POST /api/v1/admin/agent/problem-imports` creates `problem_import` runs and returns the existing draft creation response shape. The model step is recorded as `extract_rewrite`, then the existing validation, repair, slug, persistence, and official-solution checks run as before.
- Imported drafts persist admin-only source metadata in `problem_drafts.source_metadata_json` through Alembic revision `20260606_0008`: kind, source URL, raw material, raw length, import notes, and rewrite policy.
- The import prompt requires extraction, FastOJ adaptation, and rewritten statements, sample explanations, and official solutions instead of copying the pasted material. Public problem APIs and normal AI assistance contexts do not return imported raw material.
- Admin draft list/detail responses include source metadata, so the UI can show an `导入` chip, source summary, raw length, notes, and a collapsible raw-material preview for administrators.
- README, README.zh-CN, acceptance harness, and project-guide docs now describe the import workflow, source metadata boundary, frontend admin tab, and migration note.
- Verification passed: `uv run ruff check .`; `uv run pytest` (183 passed, existing FastAPI `regex` warnings); `cd frontend && npm test` (10 files / 32 tests, existing jsdom canvas notices); `cd frontend && npm run build` (existing large chunk warnings).

## 2026-06-06 Workbench Editor Control Polish

- Custom run-case deletion now lives on each case tab as a top-right close control; the previous standalone delete button below the input/expected-output column was removed.
- The case-tab close control is hidden until hover or keyboard focus within the tab, reducing visual noise while keeping deletion accessible.
- Code-template reset and run-case reset use a reset-arrow SVG instead of a text-only `R` glyph. No new icon package was added; the project still uses local lightweight icons.
- The workbench toolbar now has a persisted autocomplete toggle. It writes `fastoj.completionEnabled` to local storage and updates Monaco quick suggestions, trigger-character suggestions, parameter hints, and word-based suggestions at runtime.
- The admin Problem Agent `constraints` field is now a wider multiline textarea, matching the backend's 2000-character request field and giving admins room to describe desired problem requirements.
- `frontend/src/components/RunResultPanel.test.tsx` now covers tab-level case deletion.
- Verification passed: `uv run ruff check .`; `uv run pytest` (179 passed, existing FastAPI `regex` deprecation warnings); `cd frontend && npm test` (9 files / 29 tests, existing jsdom canvas notices); `cd frontend && npm run build` (existing large chunk warnings). A local browser DOM check against `http://127.0.0.1:5173` confirmed the SVG reset buttons, autocomplete toggle persistence, hover-revealed case close buttons, and tab-level delete controls.

## 2026-06-06 Problem Statement Detail Pass

- The bundled seed catalog remains 106 problems: 100 canonical Hot 100 entries plus 6 AI/ML exercises. The temporary local `print-test` and `print-qiu-qiu` problems are intentionally not part of seed data; the local database was cleaned back to 106 problems with those extra slugs removed.
- Seed descriptions are now expanded through `backend/scripts/problem_statement_details.py`. The expansion uses public catalog metadata and slug-specific rules to clarify the problem meaning, not the platform contract.
- Generated statements intentionally do not repeat function signatures, JSON-line mechanics, hidden-test language, stdin/stdout guidance, or generic edge-case advice. They focus on task rules, domain representation, tie-breaking, and ordering where those are part of the problem.
- Chinese localized problem details now use `frontend/src/lib/problemStatementZh.ts` to add the same concise semantic clarification, so Chinese mode no longer collapses detail pages into one-line summaries.
- Several Hot 100 descriptions that still said "print" now say "return" to match function-mode behavior; binary-tree wording now says level-order array instead of JSON protocol language.
- Monaco editor cleanup in `frontend/src/components/CodeEditor.tsx` now clears the editor ref after disposal, preventing the blank editor seen under React StrictMode effect remounting.
- Verification passed: `uv run ruff check .`; `uv run pytest` (179 passed, existing FastAPI `regex` deprecation warnings); local seed normalized 106 existing problems and no extra print slugs remained; `cd frontend && npm test` (9 files / 28 tests, existing jsdom canvas notices); `cd frontend && npm run build` (existing large chunk warnings).

## 2026-06-06 Shared Discussions And Workbench History Polish

- Problem discussions are now persisted server-side through the new `problem_discussions` table and Alembic revision `20260606_0007`. `GET /api/v1/problems/{problem_id}/discussions` returns recent public-problem posts; `POST /api/v1/problems/{problem_id}/discussions` requires authentication.
- The workbench discussion tab no longer writes localStorage notes. It loads shared discussion with TanStack Query, posts to the API, updates the query cache after successful posting, and keeps copy warning users not to paste hidden testcase content.
- Admin problem deletion now removes related discussion rows alongside testcase, submission, testcase-result, solution, and draft-link cleanup.
- Submission trail cards are expandable. Expanding a row lazily fetches the owner-scoped submission detail endpoint and displays the exact submitted code without adding code to the submission list response.
- The left/right workbench rails can be dragged open even when collapsed. The snap-close threshold is narrower (`88px`), so near-edge drags must be closer before auto-collapsing.
- Verification passed: `uv run ruff check .`; `uv run pytest` (177 passed, existing FastAPI `regex` deprecation warnings); `cd frontend && npm run build` (existing large chunk warnings); `cd frontend && npm test` (9 files / 26 tests).

## 2026-06-02 Frontend Chunk Optimization

- The frontend now lazy-loads heavy UI modules from the single `main.tsx` entry: code editor, run result panel, AI panel, judge timeline, submission trail, solution code block, training graph, auth page, and settings page.
- Monaco is imported through the ESM editor API with explicit `editor.worker?worker` setup and only FastOJ language contributions. The editor remains lazy-loaded from the workbench.
- Shiki no longer uses the full default bundle. `CodeBlock` dynamically imports `shiki/core`, the JavaScript regex engine, `github-dark`, and only the requested supported solution language, with cached highlighters per language.
- The main production `index-*.js` chunk is now 499.81 kB, down from about 1.25 MB. `npm run build` still prints Vite's large chunk warning because lazy-loaded Monaco `editor.api2` and the Shiki C++ grammar chunk are larger than 500 kB; `chunkSizeWarningLimit` was intentionally not raised.
- Verification passed: `cd frontend && npm run build`; `cd frontend && npm test` (9 files / 26 tests); `uv run ruff check .`; `uv run pytest` (176 passed).

## 2026-06-02 Worker Parent/Child Judge Hardening

- Judge worker now uses a parent/child model by default. The parent keeps heartbeat, pending reclaim, Redis task intake, active-task markers, and hard-timeout supervision; each child processes exactly one judge task through `JudgeTaskConsumer`.
- New config: `JUDGE_CHILD_PROCESS_ENABLED`, `JUDGE_TASK_HARD_TIMEOUT_SECONDS`, `JUDGE_CHILD_TERMINATE_GRACE_SECONDS`, and `JUDGE_ACTIVE_TASK_TTL_SECONDS`. Local and production Compose pass these into the worker; production `.env` can tune them.
- Active task markers live under `judge:worker:active-task:*` and include consumer, stream message id, submission id, progress, start time, last progress time, and deadline. They are observational only; `claim_pending` still avoids stealing from live workers.
- Parent handles child timeout, crash, spawn/start failure, and shutdown race cases. On hard timeout it terminates/kills the child, then removes Docker judge containers labelled with the same submission/message id before retrying or dead-lettering the Redis message.
- Retry/dead-letter now uses a Redis Lua script that `XACK`s and conditionally `XADD`s atomically. If the original message is already ACKed by a child or another recovery path, parent-side late failure handling no-ops instead of creating duplicate retry work or overwriting status.
- Duplicate execution is safer: if testcase results already exist, the judge summarizes persisted rows instead of writing duplicates, and submission status updates use row locks before accepted-count increments.
- Residual risk: parent hard-kill can still interrupt child cleanup at awkward moments; the parent now removes matching labelled containers, but production should still monitor `fastoj_judge_*` leftovers. A database-level unique constraint on `(submission_id, testcase_id)` remains a future hardening option.
- Verification passed: `uv run ruff check .`; `uv run pytest` (176 passed); `cd frontend && npm run build`; `cd frontend && npm test` (9 files / 26 tests); `docker compose config`; production config validation with placeholder env; `docker compose up --build -d api worker`; API health at `http://127.0.0.1:8010/api/v1/health`; `docker compose ps --format json` reported API, worker, PostgreSQL, and Redis healthy.

## 2026-06-02 Production Judge Dispatch Hardening

- Judge inline fallback is now an explicit dispatch policy. It follows `DEBUG` by default, can be overridden with `JUDGE_INLINE_FALLBACK`, and is set to false in both local and production Docker Compose.
- Production submissions require the Redis Streams worker path. If Redis or a live judge worker is unavailable, submit/run returns `503 Judge service unavailable` rather than executing `JudgeTask` inside the API process.
- Queue `XADD` success is treated as dispatch success; status pub/sub failures after enqueue are logged but do not cause inline duplicate judging.
- Worker heartbeat now refreshes in a background thread during long judge tasks. Pending reclaim now processes claimed payloads and skips tasks owned by consumers that still have heartbeat.
- Worker retry handling no longer marks submissions terminal `SE` before retries are exhausted; terminal errors are written only on final failure/dead-letter.
- The workbench discussion tab is now labeled as browser-local notes, safely handles corrupt local storage, and disables local posting while logged out. There is still no shared server-backed discussion model/API.
- Verification passed: `uv run ruff check .`; `uv run pytest` (162 passed); `cd frontend && npm run build`; `cd frontend && npm test` (9 files / 26 tests); `docker compose config`; `docker compose up --build -d api worker`; API health at `http://127.0.0.1:8010/api/v1/health`; `docker compose ps` reported API, worker, PostgreSQL, and Redis healthy.

## 2026-06-01 CI/CD And Tencent Cloud Deployment Prep

- GitHub Actions now has `.github/workflows/ci.yml` for backend lint/tests and frontend build/tests on PRs and `master` pushes.
- `.github/workflows/deploy.yml` now runs a quality gate, builds API/worker/judge images in GitHub Actions, pushes them to GHCR, SSHes to the Tencent Cloud server as `ubuntu`, uploads `docker-compose.prod.yml`, pulls images, and restarts services.
- Production deployment uses `/opt/projects/fastoj/.env` plus `docker-compose.prod.yml`; the server no longer needs to build source locally during normal deploys.
- Local and server runtime configuration intentionally use the same filename, `.env`. Local `.env` comes from `.env.example`; server `.env` comes from `.env.prod.example`. `.env.dev` is not required for the normal local-plus-server workflow.
- Local Compose now exposes PostgreSQL, Redis, and API ports through `.env` variables (`POSTGRES_PORT`, `REDIS_PORT`, `FASTOJ_PORT`) with loopback defaults.
- Chinese deployment steps live in `docs/DEPLOYMENT.md`, including required GitHub secrets, Tencent Cloud server preparation, first seed/admin commands, and reverse-proxy guidance.
- Docker Compose config validation passed for local `.env.example` and production `.env.prod.example`; production Compose was tightened to avoid passing unrelated `.env` keys into containers.

## 2026-05-29 Account-Backed Locale Preference

- User profiles now persist `locale` (`zh`/`en`) through a new `users.locale` column and `/api/v1/auth/me` response/update support.
- Registration records the active UI language. Header/settings language changes update local storage immediately and sync to the signed-in account when available.
- Guest users still work without an account preference: the frontend uses a normalized local-storage value, then browser language, then Chinese as the final fallback.
- The frontend sets `<html lang>` from the active locale, clears stale AI copilot content on language changes, and requires explicit locale arguments for AI/solution API methods.
- Tag search normalization now accepts Chinese commas and common case variants before querying/filtering.
- Verification for this batch: `uv run ruff check .` passed; `uv run pytest` passed with 141 tests; `cd frontend && npm run build` passed; `cd frontend && npm test` passed with 9 files / 25 tests.

## 2026-05-29 Multi-Language Authoring Draft Solutions

- Admin Problem Authoring Agent requests now accept `target_languages` while keeping the legacy `target_language` field for compatibility.
- Problem draft payloads and API responses now include `official_solutions`, a per-language list of official solution code and explanation. The legacy single official-solution fields remain populated from the primary solution.
- A new Alembic migration adds `problem_drafts.official_solutions_json`; existing drafts fall back to their legacy single official solution.
- Authoring validation requires all requested solution languages to be present and runs each official solution language through the sandbox. Validation reports show solution language per case without exposing hidden testcase content.
- Draft approval creates one official `Solution` row per draft language.
- The admin authoring UI now has target-language checkboxes, a per-language official solution editor, and per-language validation chips in testcase details.
- Verification for this batch: `uv run ruff check .` passed; `uv run pytest` passed with 137 tests; `cd frontend && npm run build` passed; `cd frontend && npm test` passed with 9 files / 23 tests.

## 2026-05-29 Dynamic AI Profile Availability

- AI model choices are now served by `GET /api/v1/ai/profiles` instead of being hard-coded in the frontend.
- The API checks `default`, `deepseek`, and `qwen-local` profile availability with configuration preflight, `/models` probing, a chat-completions fallback, short timeouts, and a 60-second cache.
- Startup schedules profile checks in the background and never fails just because an AI provider is offline.
- `model_profile=default` routes to the first healthy profile in this order: default config, DeepSeek, local Qwen.
- Regular users only receive available profiles; admins receive all profiles plus safe unavailable reasons for authoring setup.
- Verification for this batch: `uv run ruff check .` passed; `uv run pytest` passed with 127 tests; `cd frontend && npm run build` passed; `cd frontend && npm test` passed with 9 files / 22 tests; `docker compose up --build -d api` rebuilt and started the API; `docker compose ps api` reported healthy; health passed at `http://127.0.0.1:8010/api/v1/health`.

## 2026-05-29 Admin Authoring And Testcase Management

- Problem Authoring Agent draft creation now attempts bounded self-repair: after a failed validation, it can call the model up to two more times with a safe repair context before persisting the final draft.
- The repair context contains failed check names, public sample diagnostics, and aggregate case summaries only. Hidden testcase input/output remains out of repair prompts, run output, and validation reports.
- The admin draft preview now includes testcase details with filters for all/public/hidden/failed cases, so administrators can inspect generated inputs and expected outputs before approving a draft.
- Formal problem management now has admin-only testcase CRUD endpoints and a frontend testcase manager for input, output, hidden/sample flags, score, and order.
- Formal problem management now supports deleting published problems; deletion removes related testcases, solutions, submissions, and testcase results, while approved draft records keep their history with the approved-problem link cleared.
- The published-problem delete action is intentionally available only inside the edit panel now; list-row/card delete controls were removed to reduce accidental deletes.
- Admins can edit a failed authoring draft and use the save-and-revalidate action to rerun sandbox validation before approval.
- Draft target languages are now persisted on `ProblemDraft`; manual saves and revalidation require official solution code and explanation for each selected language.
- Draft review now supports AI-filling one missing official-solution language at a time. The solution-generation prompt includes current draft fields, public samples, and existing official solutions, but omits hidden testcase content and redacts hidden values from free text.
- Draft detail responses include grouped run history, so original model generation, bounded repair attempts, manual edits, approval, and rejection remain inspectable in the admin timeline.
- Authoring requests and draft editing now include a `both` mode for problems that should expose both function-mode and ACM-mode practice.
- `both` mode now uses one canonical function-style official solution per language. Validation wraps that function solution only; ACM practice shares the same JSON-argument input/output contract instead of requiring a second stdin/stdout reference program.
- Formal problem editing now supports slug, mode, function signature, ACM input/output formats, time/memory limits, multilingual official solution CRUD, per-language AI fill, and save-and-revalidate against all current official solutions.
- Hidden and sample testcase flags are mutually exclusive in backend create/update paths and in the admin UI.
- Disabled-user access tokens and judge WebSocket connections are rejected; normal users cannot run or submit private problems through direct API calls.
- Manual draft slug edits now ignore failed, rejected, and historical approved drafts; true duplicate active slugs still show a visible error instead of silently appending `-2`/`-3`.
- Draft action buttons now prevent approving unsaved local edits, ask for publish/reject confirmation, and only enable cancel when local edits exist.
- Rejected drafts now render as an explicit status chip in the left draft list, and the formal-problem edit panel has a cancel action.
- Authoring validation now requires at least one public testcase and one total testcase. Hidden cases remain recommended for non-trivial problems but are not forced for simple drafts.
- Function-mode authoring validation treats raw string output and JSON string-literal expected output as equivalent, covering no-input string-return tasks such as `print-qiu-qiu`.
- Docker Compose now gives the API service access to the Docker judge runtime so admin draft validation can run synchronously in the API container.
- README and README.zh-CN describe the new admin testcase management and bounded authoring-agent repair behavior.
- Verification for this batch: `uv run ruff check .` passed; `uv run pytest` passed with 149 tests; `cd frontend && npm run build` passed; `cd frontend && npm test` passed with 9 files / 25 tests; `docker compose up --build -d api` rebuilt the API image; `docker compose ps api` reported API healthy; health passed at `http://127.0.0.1:8010/api/v1/health`.

## 2026-05-29 Workbench Run Panel And Auth Feedback

- Workbench public runs now support editable public run inputs. The new result panel below Monaco shows sample input, official/reference generated expected output, the user's actual output, and line-level diffs with mismatches highlighted.
- Async judging now uses a Redis worker heartbeat. The original local fallback avoided permanently pending submissions; as of 2026-06-02 that fallback is debug/local-only and production returns 503 when the queue or worker path is unavailable.
- Frontend polling now appends a terminal result/error event when it observes a finished submission, so the judge timeline recovers even if the WebSocket result event was missed.
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
- Verification on 2026-05-29: `uv run ruff check .` passed; `uv run pytest` passed with 135 tests; `cd frontend && npm run build` passed; `cd frontend && npm test -- --run` passed with 9 files / 23 tests; `docker compose up --build -d api worker` passed; API health returned `{"status":"healthy","app":"FastOJ"}` at `http://127.0.0.1:8010/api/v1/health`; a real `print-qiu-qiu` function-mode run returned `result: ac`; a real custom-run smoke for Majority Element `[1,2,2]` returned `expected_output: 2`, `actual_output: 2`, and `result: ac`.

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
- `uv run ruff check .`: passed after the SSE/Markdown/dual-sample work.
- `uv run pytest`: passed, 219 tests passed with 2 FastAPI `regex` deprecation warnings.
- `cd frontend && npm test`: passed, 10 files and 42 tests.
- `cd frontend && npm run build`: passed, with existing large chunk warnings.
- `docker compose up --build -d api worker`: passed; API and worker report healthy.
- `docker compose exec -T api uv run alembic -c backend/alembic.ini upgrade head`: passed.
- `docker compose exec -T api uv run python -m backend.scripts.repair_online_least_squares_problem`: passed twice, each time reporting `repaired 1 problem(s), 4 draft(s)`.
- Container service-layer check confirmed the logistics problem is `mode=both`; ACM sample input starts with `8 / ADD 10 35`, while Function sample input is a JSON string array.

## Failed Commands And Error Summary

- The latest “智能物流定价引擎（在线学习）” import failure was not a model JSON failure. The structured import created drafts, but validation failed before running cases because the admin selected `python/cpp/java` while the draft only had a Python official solution. The fix now generates Python/C++/Java for the recognized online least-squares problem and falls back to reliable available languages for generic structured imports.
- Admin Agent create/import/retry now return a running `run_id/session_id` in the HTTP path and execute as background tasks. The frontend subscribes to `/api/v1/admin/agent/runs/{run_id}/events` via fetch-based SSE and merges `snapshot`, `step`, `draft_ready`, and `run_status` events into the selected session timeline.
- Problem statements, hints, sample explanations, official solutions, discussion bodies, Agent messages, and admin previews now render Markdown through a shared sanitized `MarkdownBlock`. Storage remains plain Markdown text.
- `testcases.io_metadata_json` stores mode-specific views for the same logical testcase. `GET /api/v1/problems/{id}?judge_mode=acm|function` returns current-mode `sample_testcases[].input/output` and also includes optional `acm_*` / `function_*` fields for debugging and UI display.
- The published “智能物流定价引擎（在线学习）” problem and 4 related drafts were repaired in the Docker DB with Markdown content and ACM/Function sample views by running `docker compose exec -T api uv run python -m backend.scripts.repair_online_least_squares_problem`. Re-running the script is idempotent.
- Java ACM validation initially failed during the fix because the sandbox writes Java code to `Solution.java`; declaring `public class Main` caused CE. The generated ACM Java solution now uses `class Solution` with `main`.
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

1. Browser-check the new Admin Agent SSE timeline with a real import: creation should immediately show a running run, then stream plan/validation/persistence steps without page refresh.
2. Convert `docs/ACCEPTANCE_HARNESS.md` into a Playwright/equivalent browser suite covering auth, library search/filter, function and ACM run/submit, WebSocket-first status, polling fallback, AI locale behavior, settings, admin, and screenshot smoke.
3. Finish the remaining browser manual acceptance items not fully automated in this batch: register/login redirect, token-expiry alert, settings save/error with typed form data, admin mutation restore paths, and explicit polling fallback simulation.
4. Inspect the Chinese UI in a real browser for any remaining mixed-language problem text; move problem statement/solution translations from temporary frontend/backend maps to backend-managed localized fields when the content model is finalized.
5. Expand C function-mode harnesses for AI tasks that require matrices or strings, or hide C function mode for those tasks until supported.
6. Split Monaco/Shiki into lazy chunks to reduce initial frontend bundle size.
