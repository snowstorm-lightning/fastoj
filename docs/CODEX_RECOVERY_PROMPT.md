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
- Finish tests, builds, Docker verification, README, and final summary.

Immediate next steps:
1. Start Docker Desktop Linux engine.
2. Re-run docker compose up --build -d.
3. Execute the README browser manual acceptance path.
4. Review Alembic baseline migration against any existing database.
5. Before ending again, update docs/CODEX_HANDOFF.md, docs/CODEX_PROGRESS.md, docs/CODEX_RECOVERY_PROMPT.md and either commit a clean checkpoint or refresh docs/codex-checkpoint.patch.
```
