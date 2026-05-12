# Recovery Prompt

Copy this into the next Codex session if work is interrupted:

```text
Continue the FastOJ upgrade task in C:\Users\Lightning\LearningProjects\fastoj. Do not restart from scratch. First read docs/CODEX_HANDOFF.md, docs/CODEX_PROGRESS.md, and docs/dependency-audit.md. Then inspect git status and continue from the current WIP.

Current target: upgrade FastOJ from a FastAPI + PostgreSQL + Redis + Docker Worker + static frontend OJ prototype into an AI-explainable interview training OJ platform.

Important constraints:
- Keep hidden testcase input/expected/actual strictly out of normal user APIs and AI prompts.
- AI provider is only OpenAI-compatible, with AI_PROVIDER=disabled by default.
- Use Redis Streams/consumer groups for judge queue, with ack/retry/dead-letter/idempotency.
- Worker must publish judge status through Redis pub/sub; API relays to WebSocket clients.
- Production must not fall back to host subprocess execution unless FASTOJ_ALLOW_UNSAFE_LOCAL_EXECUTION=true.
- Frontend stack is Vite + React + TypeScript + Tailwind + Monaco + TanStack Query + Zustand + Zod + xterm + Shiki + @xyflow/react + @chenglou/pretext.
- Docker Compose now builds and starts successfully. API health returned HTTP 200.
- Existing prototype DB volumes are handled by backend/scripts/migrate_or_stamp.py, which stamps the Alembic baseline if core tables already exist and alembic_version is absent.

Immediate next steps:
1. Run the browser manual acceptance path at http://localhost:8000.
2. Exercise register/login, problem filters, run, submit, WebSocket status, AI disabled 503 path, and hidden-case redaction.
3. If preparing for production, review the Alembic baseline/stamp strategy against the target database before rollout.
4. Before ending again, update docs/CODEX_HANDOFF.md, docs/CODEX_PROGRESS.md, docs/CODEX_RECOVERY_PROMPT.md and either commit a clean checkpoint or refresh docs/codex-checkpoint.patch.
```
