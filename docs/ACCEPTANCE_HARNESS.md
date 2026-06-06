# FastOJ Acceptance Harness

Updated: 2026-06-06

This document is the repeatable acceptance harness for the current product shape. It intentionally avoids printing or storing hidden testcase input, expected output, actual output, JWTs, `.env` values, or AI provider raw responses.

## Automated Baseline

Run these before handing off substantial changes:

```bash
uv run ruff check .
uv run pytest
cd frontend && npm run build
cd frontend && npm test
```

When judge, worker, WebSocket, sandbox, or real submission behavior changes, also run:

```bash
docker compose up --build -d api worker
docker compose ps
```

Then check:

```text
GET http://127.0.0.1:8000/api/v1/health
```

Expected result: HTTP 200 with a healthy status.

## Browser Smoke Matrix

Use the in-app browser or an equivalent local browser against `http://127.0.0.1:8000`.

### Anonymous And Auth

- Open the app and verify the problem library renders.
- Toggle the problem library between card layout and OJ-style list layout; reload and verify the chosen layout persists.
- Register a disposable local account with a non-production email address.
- Verify validation errors render as readable text and never as `[object Object]`.
- Log in with the disposable account.
- Log out and log back in.
- Switch Chinese/English locale and verify navigation/auth/settings copy stays natural in the active locale.

### Problem Library

- Search `Two Sum`; expected: the Two Sum problem remains visible.
- Switch to Chinese and search `两数之和`; expected: the localized Two Sum card remains visible.
- Filter by difficulty and by a public tag.
- Move pagination forward/backward where enough data exists.
- Click a training graph node and verify the library reopens with the corresponding tag filter.

### Workbench

- Open a function-mode problem.
- Switch programming language.
- Toggle function mode and ACM mode where supported.
- Verify the central editor remains usable at 1280 px wide, with no clipped AI/detail panel.
- Toggle code completion from the workbench toolbar, reload, and verify the preference persists.
- Run public cases from the starter; a failure is acceptable if the starter is intentionally incomplete.
- Add a custom run case and verify the case tab close button appears on hover/focus and deletes the case.
- Replace starter code with a known local test solution and run public cases again.
- Submit once and verify status moves through pending/judging/result using WebSocket-first status with polling fallback available.
- Verify the judge details show public cases only. Hidden testcase rows may show aggregate counts or hidden labels only, never hidden input, expected output, or actual output.

### AI Copilot

- Request a hint in the active locale.
- Request an explanation after a failed public run.
- Run or submit again with corrected code.
- Expected: stale hint/explain/review/chat state is cleared for the new submission, and late AI responses from the old submission do not reappear.
- Request review and chat only after a current submission exists.

### Settings

- Save profile fields with valid disposable data.
- Trigger a validation error with invalid disposable data.
- Expected: readable error text, no `[object Object]`, no tokens, and no provider payloads.

### Admin

- Log in as a locally bootstrapped disposable admin.
- Open the admin console.
- Verify user list search, role filter, status filter, and pagination.
- Toggle a disposable user's active state and restore it.
- Change a disposable user's role only if the test environment can safely restore it.
- Verify problem list search, difficulty filter, visibility filter, and pagination.
- Change a problem difficulty and restore it.
- Toggle problem visibility and restore it.
- Verify hidden testcase content is not shown; counts are acceptable.
- Generate or select a validation-failed problem draft and verify the validation area shows failed checks, aggregate counts, failed-case counts, and sandbox statuses only. It must not show hidden testcase bodies, expected outputs, actual outputs, raw stderr, or provider payloads.
- Open the `导入题目` tab, paste a disposable public-domain or self-written problem-style paragraph longer than 20 characters, add optional source URL/import notes, and verify `导入为草稿` calls the admin import flow.
- Select the imported draft and verify it shows a `导入` chip, source summary, raw material length, and a collapsible admin-only raw preview.
- Verify published/public problem views do not show imported raw material or source metadata.
- Verify the current admin surface exposes user/problem/testcase/solution management and draft review basics; submission audit, judge queue, and system health remain planned follow-ups.

## Visual Screenshot Inventory

Capture or visually inspect these screens after frontend layout changes:

- Learner dashboard/current library landing state.
- Problem library with empty, loading, filtered, and populated states.
- Workbench at 1280 px and mobile/tablet breakpoints.
- AI Copilot panel after idle, failed run, and accepted submit states.
- Judge timeline and submission trail.
- Training graph.
- Auth page.
- Settings page.
- Admin dashboard/users/problems panels.
- Admin original authoring and imported draft panels.
- Error states for auth/settings/admin validation.

## Safety Checks

- Search visible browser text after a full submit for hidden testcase sentinels used in local tests. The expected result is no hidden input, expected output, or actual output.
- Do not save screenshots or logs that contain JWTs, `.env` values, provider responses, or hidden testcase content.
- Do not send hidden testcase content to AI provider requests. AI context may include public samples, user code, aggregate verdict, and safe hidden-failure summaries only.
- Imported raw material may be sent only through the admin import flow and must remain admin-only metadata afterward. It must not appear in public problem responses, learner AI prompts, screenshots, or logs.
- Admin UI access is not a security boundary. Confirm backend routes still use server-side admin checks.

## Automation Roadmap

No Playwright dependency is added in this batch. The current minimum harness is the automated baseline plus the browser smoke matrix above. A future Playwright suite should live under `frontend/e2e/` and cover:

- Auth happy path and validation errors.
- Problem search/filter/navigation in both locales.
- Function and ACM run/submit flows.
- WebSocket-first status plus polling fallback.
- AI locale behavior and stale-state prevention.
- Settings save/error behavior.
- Admin user/problem management with server-side permission tests.
- Screenshot smoke baselines for library, workbench, AI panel, graph, settings, and admin.
