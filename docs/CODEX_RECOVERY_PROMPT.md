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
- Frontend information architecture is split into problem library, dedicated auth page, account settings, core function-mode workbench, and training graph. The workbench has resizable/collapsible statement/result sidebars, function/ACM modes, public cases, solution, judge terminal, submission trail, discussion, AI Copilot, and static visual panels.
- Pretext is wrapped only through frontend/src/lib/textLayout.ts and is used for problem cards, graph nodes, and submission trail summaries.
- Docker Compose builds and starts. After Docker Desktop was restarted on 2026-05-14, API and worker reported healthy, HTTP health/frontend returned 200, and worker-in-container Docker SDK access returned True with requests 2.31.0.
- Docker archive injection now works in worker-in-container mode by copying source/stdin into an ephemeral container workspace instead of tmpfs. Real API public run and full submit returned AC for Two Sum function mode and Valid Parentheses ACM mode after seed normalization and async consumer fixes.
- Judge runtime includes Python numpy==2.2.6 and CPU torch==2.7.1+cpu.
- AI provider supports DeepSeek API and local OpenAI-compatible servers through the same `AI_PROVIDER=openai_compatible` path. Store real keys in `.env` or deployment env vars; `.env` and `.env.*` are gitignored, and `.env.example` is safe.
- Existing prototype DB volumes are handled by backend/scripts/migrate_or_stamp.py, which stamps the Alembic baseline if core tables already exist and alembic_version is absent.
- Latest UI/mode work adds multi-language function-mode judge wrappers/starters for Python, C++, Java, JavaScript, TypeScript, Go, and selected simple C signatures, interview-list and AI algorithm seed problems, dedicated login/register page, smoother resizable sidebars, clearer button titles/tooltips, single-button function/ACM mode toggle, frontend Chinese/English i18n, localized verdict hover explanations, and login redirect for unauthenticated run/submit.
- Docker sandbox compiled-language execution now uses final-program stdin redirection (`< input.txt`) rather than piping stdin into compile commands, and `/tmp/work` is chmod-adjusted so the `nobody` runner can create compiled binaries without adding capabilities.
- Latest WIP adds a localized token-expiry alert before redirecting to login, fixed-viewport workbench scrolling with internal panel scroll, public sample explanations, expanded seeded testcase counts, Softmax verification, and AI provider response normalization so DeepSeek scalar/list variations do not break hint/explain/review.
- Current WIP adds a controlled AI model selector (`default`, `deepseek`, `qwen-local`), backend named AI profiles, localized graph labels, structured sample cards, local discussion/settings views, account profile editing, admin-only user/problem management, active-locale AI requests, Chinese official-solution explanations for seeded problems, removal of visible old-site wording, and backend/frontend acceptance-rate clamping so invalid historical counts cannot show rates above 100%.
- `llama-server` is not installed in the current PATH. The local Qwen profile is wired, but the user needs to install/start an OpenAI-compatible Qwen server before the `qwen-local` selector can return real responses.
- Latest user direction: this is a new project. Do not preserve old prototype testcase input compatibility. That compatibility has been removed from function-mode code; continue targeting JSON-line function-mode testcase data only and normalize/discard incompatible prototype DB rows instead of reintroducing legacy parsing.
- Current WIP warning: full browser manual acceptance still needs to be run after the latest account/admin/AI-locale/function-starter edits. Public/full API judging paths for function and ACM mode are fixed. `127.0.0.1:8000` passes health/static checks, API and worker are healthy, and a real Docker-backed Two Sum C++ function-mode public run returned AC.

Immediate next steps:
1. If local Qwen responses are required, stop and ask the user to install/start `llama-server` or another OpenAI-compatible Qwen server.
2. Run the browser manual acceptance path at http://127.0.0.1:8000.
3. Exercise register/login redirect, token-expiry alert, language switch, problem filters, sidebar resize/collapse, function mode across languages, ACM mode, public run, full submit, WebSocket status, DeepSeek/Qwen-profile AI hint/explain/review in Chinese, discussion/settings/admin, graph localization, and hidden-case redaction.
4. Inspect the Chinese UI in a real browser for any remaining mojibake or mixed-language problem text.
5. Decide whether to move localized problem statements/solutions from frontend/backend temporary maps to backend-managed localized fields before adding more content.
6. If preparing for production, review the Alembic baseline/stamp strategy against the target database before rollout.
7. Before ending again, update docs/CODEX_HANDOFF.md, docs/CODEX_PROGRESS.md, docs/CODEX_RECOVERY_PROMPT.md and either commit a clean checkpoint or refresh docs/codex-checkpoint.patch.
```
