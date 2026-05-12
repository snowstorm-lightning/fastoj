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
- [ ] Add/finish tests for disabled provider, mock provider, hidden-test redaction, ownership checks.
- [x] Add/finish tests for disabled provider, mock provider, hidden-test redaction, ownership checks.
- [ ] Validate OpenAPI output in a running server.

## Judge Queue And Worker

- [x] Started Redis Streams queue migration.
- [x] Added consumer group creation.
- [x] Added ack helper.
- [x] Added retry/dead-letter helper.
- [x] Added pending reclaim helper.
- [x] Updated worker loop to read stream messages.
- [x] Added duplicate testcase result guard.
- [x] Add retry/dead-letter unit tests.
- [ ] Validate dead-letter behavior with real Redis.

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
- [x] Added read-only root filesystem and tmpfs work dirs.
- [x] Added non-root user.
- [x] Added output truncation.
- [x] Added CE/TLE/MLE/RE/SE mapping improvements.
- [ ] Validate with Docker judge image.
- [x] Add sandbox hidden-output isolation test.

## Frontend

- [x] Vite + React + TypeScript scaffold.
- [x] Tailwind/PostCSS config.
- [x] Zod schemas.
- [x] API client.
- [x] Zustand localStorage draft/cache store.
- [x] Pretext adapter.
- [x] Monaco editor component.
- [x] AI Copilot panel.
- [x] xterm judge timeline.
- [x] Training graph with @xyflow/react.
- [x] Submission trail.
- [x] Wire Shiki code block rendering.
- [ ] Make graph node click drive actual tag filtering.
- [x] Run and fix full frontend build/test after app implementation.
- [x] Add frontend smoke tests for schemas, textLayout, graph, copilot.

## Database And Migrations

- [x] Added Alembic env and script template.
- [x] Added initial baseline migration.
- [x] Avoided unconditional production `Base.metadata.create_all`; now only runs in debug.
- [ ] Validate migration against PostgreSQL.
- [x] Update README with migration workflow.

## Documentation

- [x] Dependency audit doc.
- [x] Checkpoint handoff doc.
- [x] Progress checklist doc.
- [x] Recovery prompt doc.
- [x] README full rewrite.
- [ ] Final summary.

## Verification

- [x] Phase 0 `uv sync`.
- [x] Phase 0 frontend `npm run build`.
- [x] Phase 0 frontend `npm test`.
- [x] `uv run ruff check .`.
- [x] `uv run pytest`.
- [x] Full frontend `npm run build`.
- [x] Full frontend `npm test`.
- [ ] `docker compose up --build` blocked: Docker Desktop Linux daemon not running.

## Checkpoint

- [x] Ran `git status`.
- [x] Ran `git diff --stat`.
- [x] Created handoff/progress/recovery files.
- [x] Generated `docs/codex-checkpoint.patch`.
- [x] Continue original task after checkpoint.
