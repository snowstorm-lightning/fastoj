# FastOJ

English | [简体中文](README.zh-CN.md)

Live demo: [fastoj.snowstormlightning.top](http://fastoj.snowstormlightning.top)

FastOJ is a full-stack, AI-assisted online judge for interview practice. It
combines a LeetCode-style learner experience with a production-shaped backend:
FastAPI, PostgreSQL, Redis Streams, Docker sandbox execution, a React/Monaco
workbench, bilingual UI, admin authoring workflows, and AI feedback that is
explicitly isolated from hidden tests.

The project is designed to be useful in two ways: it is a runnable practice
platform with a 108-problem seed catalog, and it is a compact systems project
for studying judge pipelines, sandboxing, async workers, AI provider routing,
and product-grade frontend workflows.

## Why It Stands Out

- **Real judge pipeline.** Submissions go from FastAPI to Redis Streams, then to
  a worker supervised with parent/child task isolation, and finally into a
  locked-down Docker sandbox. Production does not execute untrusted code with
  host `subprocess`.
- **Function mode and ACM mode.** Learners can solve starter-frame function
  problems or classic stdin/stdout problems. Dual-mode drafts can keep both
  views aligned from the same logical testcase metadata.
- **AI that respects the OJ boundary.** Hints, explanations, reviews, and chat
  use public samples, verdicts, user code, and safe aggregate details. Hidden
  testcase input, expected output, and actual output are not exposed to users or
  sent to model providers.
- **A product frontend, not just forms.** The React UI includes a searchable
  library, card/list layouts, Monaco editing, split result panels, output diffs,
  judge timelines, AI copilot, account settings, shared discussions, a React Flow
  training graph, and a full admin console.
- **Admin-grade problem operations.** Administrators can generate original
  drafts, import external problem material, stream Agent traces over SSE,
  validate official solutions in the sandbox, manage users and permissions, edit
  testcase sets, revalidate drafts, and publish multilingual official solutions.
- **Provider-flexible AI.** The backend uses OpenAI-compatible profiles, with
  documented routes for hosted DeepSeek-style APIs and local Qwen through
  llama.cpp `llama-server`.
- **Deployable shape.** Docker Compose is used locally and in production, GitHub
  Actions builds API/worker images, a container registry stores images, and the
  production server pulls images instead of building source.

## Tech Stack at a Glance

| Layer | Technologies |
| --- | --- |
| Backend API | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic |
| Data and queue | PostgreSQL 14+, Redis Streams, Redis Pub/Sub |
| Judge runtime | Python Docker SDK, Docker sandbox containers, worker watchdogs, dead-letter handling |
| Frontend | React, TypeScript, Vite, Tailwind CSS, Monaco Editor, TanStack Query, Zustand, Zod |
| Rich UI | React Flow, Shiki, xterm, DOMPurify, marked, Pretext text measurement |
| AI layer | OpenAI-compatible HTTP providers, DeepSeek profiles, local Qwen/llama.cpp profile |
| Tooling and CI/CD | `uv`, `ruff`, `pytest`, `npm`, Vitest, Docker Compose, GitHub Actions, container registry |

## Product Tour

1. **Bilingual light/dark interface** - switch English/Chinese and theme from the
   top navigation. Signed-in language preference is stored on the account;
   guests use browser language plus local storage. The library, workbench,
   graph, auth flow, and admin console follow the same theme system.
2. **Problem library** - search, filter by tag/difficulty, switch between visual
   cards and a dense OJ-style list, and jump into recommended practice.
3. **Coding workbench** - read the statement, code in Monaco, edit public-run
   inputs, compare official expected output with your output, submit for hidden
   judging, and watch realtime status. Wrong answers keep the judge feedback,
   diff view, submission code, and AI follow-up in one place.
4. **AI Copilot** - request progressive hints, failed-submission explanations,
   code review, and contextual chat in the active UI language.
5. **Training graph** - browse topic nodes built with React Flow and return to
   the library with the matching tag filter applied.
6. **Admin console** - manage problems, testcase sets, users, permissions, AI
   authoring drafts, import workflows, Agent run traces, official solutions, and
   draft publication from one protected workspace.

## Page Showcase

The UI supports both light and dark themes from the top navigation. The
screenshots below use the English UI; Chinese can be toggled from the header and
is saved to the user profile after sign-in.

| Problem Library | Coding Workbench |
| --- | --- |
| ![FastOJ problem library with filters, problem cards, mode badges, and acceptance stats](docs/screenshots/library-en.png) | ![FastOJ workbench with statement panel, Monaco editor, adjustable editor/result split, editable run inputs, official expected output, output diff, and AI judge copilot](docs/screenshots/workbench-en.png) |
| Searchable practice catalog with light/dark themes, filters, card/list layouts, mode badges, and training metrics. | Focused coding surface with the statement, starter frame, adjustable editor/result split, editable sample input, official expected output, your output, diff, and AI judge assistant in one view; after a wrong run, the assistant uses the judge feedback to suggest causes and fixes. |

| Training Graph | Auth Flow |
| --- | --- |
| ![FastOJ knowledge graph with topic cards and progress counts](docs/screenshots/graph-en.png) | ![FastOJ login and registration screen with account form, confirm password, product proof chips, and auth dialogs](docs/screenshots/auth-en.png) |
| Topic map built with React Flow; clicking a node returns to the library with a tag filter applied. | Dedicated login/register screen with confirm password and clear success/error dialogs that keeps account, submissions, drafts, and AI feedback tied together. |

| Admin Console |
| --- |
| Admins get a single workspace for original problem authoring, imported-problem drafting, execution-trace review, user management, problem/content management, formal testcase management, and draft approval. Hidden testcase content and imported raw source material are visible only through admin UI/API and are not exposed to regular problem views, AI explanations, or submission logs. |

## Quick Start

The Docker Compose path is the fastest way to try the full product.

Linux/WSL prerequisites:

- Docker Engine or Docker Desktop with Linux containers enabled.
- Python 3.11+ and `uv` for host-side backend checks.
- Node.js `20.19+` or `22.12+` and npm `10+` for frontend builds.
- On WSL, keep the checkout on the Linux filesystem, for example under
  `~/projects`, not under `/mnt/c`, so bind mounts and dependency installs stay
  fast and preserve Linux file semantics.

```bash
git clone https://github.com/snowstorm-lightning/fastoj.git
cd fastoj
cp .env.example .env
docker compose up --build
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open:

```text
http://127.0.0.1:8010
```

Seed the bundled problem set:

```bash
docker compose exec api uv run python -m backend.scripts.seed_data
```

Create the first administrator from a trusted shell:

```bash
docker compose exec api uv run python -m backend.scripts.create_admin --username admin --email admin@example.com
```

The admin script prompts for a password without echoing it. For unattended local
automation, set `FASTOJ_ADMIN_PASSWORD` in the trusted execution environment
instead of passing secrets through shell history.

## Local Development

Use this path when you want to run backend and frontend processes directly. Make
sure PostgreSQL and Redis are available, or keep the Compose services running.
With the bundled Compose file, host tools reach PostgreSQL on port `5433`; the
copied `.env` from `.env.example` already sets
`DATABASE_URL=postgresql://fastoj:fastoj_secret@localhost:5433/fastoj`.

For direct backend judging, build the Docker judge runtime once:

```bash
docker compose build judge-runtime
```

Backend:

```bash
cp .env.example .env
docker compose up -d postgres redis
uv sync --extra dev
uv run alembic -c backend/alembic.ini upgrade head
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm ci
npm run dev
```

The Vite dev server can call the same-origin API by default. Set
`VITE_API_BASE_URL` only when the API runs on a separate origin.

Direct host development uses `DEBUG=true`, so the API may run judge work inline
when the async worker queue is unavailable. Docker Compose and production set
`JUDGE_ASYNC=true` with `JUDGE_INLINE_FALLBACK=false`, so a missing Redis/worker
path returns `503 Judge service unavailable` instead of moving submission load
into the API process.

The worker also runs each queued judge task in a child process by default. The
parent process keeps the Redis heartbeat, records an active-task marker, and
terminates a stuck child after `JUDGE_TASK_HARD_TIMEOUT_SECONDS` before retrying
or dead-lettering the stream message.

## AI Configuration

AI is disabled by default, so the core OJ flow works without any model server or
API key.

```bash
AI_PROVIDER=disabled
```

Hosted OpenAI-compatible provider example:

```bash
AI_PROVIDER=openai_compatible
AI_BASE_URL=https://api.deepseek.com
AI_API_KEY=your-provider-key
AI_MODEL=deepseek-v4-flash
```

Named profiles used by the in-page model selector:

```bash
AI_DEEPSEEK_BASE_URL=https://api.deepseek.com
AI_DEEPSEEK_API_KEY=your-provider-key
AI_DEEPSEEK_MODEL=deepseek-v4-flash

AI_DEEPSEEK_PRO_BASE_URL=https://api.deepseek.com
AI_DEEPSEEK_PRO_API_KEY=your-provider-key
AI_DEEPSEEK_PRO_MODEL=deepseek-v4-pro
AI_DEEPSEEK_PRO_TIMEOUT_SECONDS=120
AI_DEEPSEEK_PRO_MAX_OUTPUT_TOKENS=4000
AI_AUTHORING_REPAIR_ATTEMPTS=4

AI_QWEN_BASE_URL=http://host.docker.internal:8080/v1
AI_QWEN_API_KEY=sk-no-key-required
AI_QWEN_MODEL=qwen2.5-coder-7b-instruct-q4_k_m
```

For normal OpenAI-compatible DeepSeek API calls, use `deepseek-v4-pro` or
`deepseek-v4-flash` directly.

FastOJ exposes `GET /api/v1/ai/profiles` for the frontend model selector. The
API checks the configured profiles in the background with a short timeout and
caches availability for 60 seconds. Regular users only see currently available
profiles; administrators can also see unavailable profiles and a safe failure
reason. Selecting `default` auto-routes to the first healthy profile in this
order: default config, DeepSeek Pro, DeepSeek, then local Qwen. The admin
Problem Agent defaults to DeepSeek Pro when available, while normal user AI
controls continue to prefer `default`. AI calls still validate the provider at
request time, so a model going offline returns a normal 503 instead of breaking
API startup.

### Local Qwen Deployment

FastOJ talks to local Qwen through llama.cpp's OpenAI-compatible
`llama-server`. The tested profile uses the official
[Qwen/Qwen2.5-Coder-7B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF)
model with the `Q4_K_M` quantization and the local model id
`qwen2.5-coder-7b-instruct-q4_k_m`.

FastOJ does not ship model files or `llama-server`. Keep them outside the
repository, for example under `$HOME/Models/qwen` on Linux/WSL or
`%USERPROFILE%\Models\qwen` on Windows, so large binaries and model weights never
enter git.

Expected Linux/WSL local layout:

```text
$HOME/Models/qwen/
  llama-server  # optional when llama.cpp is installed globally
  qwen2.5-coder-7b-instruct-q4_k_m.gguf
  start-qwen-llama-server.sh
```

Expected Windows local layout:

```text
%USERPROFILE%\Models\qwen\
  llama-server.exe  # optional when llama.cpp is installed globally
  qwen2.5-coder-7b-instruct-q4_k_m.gguf
  start-qwen-llama-server.ps1
  stop-qwen-llama-server.ps1
```

Recommended Linux/WSL setup:

```bash
mkdir -p "$HOME/Models/qwen"
python3 -m pip install -U huggingface_hub
huggingface-cli download Qwen/Qwen2.5-Coder-7B-Instruct-GGUF \
  --include "qwen2.5-coder-7b-instruct-q4_k_m.gguf" \
  --local-dir "$HOME/Models/qwen"
```

If `llama-server` is installed globally, create
`$HOME/Models/qwen/start-qwen-llama-server.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

root="$HOME/Models/qwen"
server="$root/llama-server"
if [ ! -x "$server" ]; then
  server="$(command -v llama-server)"
fi

exec "$server" \
  -m "$root/qwen2.5-coder-7b-instruct-q4_k_m.gguf" \
  --alias qwen2.5-coder-7b-instruct-q4_k_m \
  --host 127.0.0.1 \
  --port 8080 \
  -c 8192 \
  -ngl 999
```

Then make it executable:

```bash
chmod +x "$HOME/Models/qwen/start-qwen-llama-server.sh"
```

Recommended Windows install path:

1. Install llama.cpp with WinGet:

   ```powershell
   winget install llama.cpp
   llama-server --version
   ```

   If `llama-server` is not found, close and reopen PowerShell so the updated
   `PATH` is loaded.

2. Create a model directory:

   ```powershell
   New-Item -ItemType Directory -Force "$env:USERPROFILE\Models\qwen"
   ```

3. Install the Hugging Face downloader:

   ```powershell
   py -m pip install -U huggingface_hub
   ```

4. Download the Q4_K_M GGUF file:

   ```powershell
   huggingface-cli download Qwen/Qwen2.5-Coder-7B-Instruct-GGUF `
     --include "qwen2.5-coder-7b-instruct-q4_k_m.gguf" `
     --local-dir "$env:USERPROFILE\Models\qwen"
   ```

5. If you installed llama.cpp with WinGet, the start script below can find it
   through `PATH`. To inspect the resolved path, run:

   ```powershell
   Get-Command llama-server
   ```

Manual binary install path:

1. Open the [llama.cpp releases page](https://github.com/ggml-org/llama.cpp/releases).
2. Download the latest Windows asset that matches the machine:
   - `Windows x64 (CPU)` for CPU-only or unknown GPU setups.
   - `Windows x64 (CUDA 12/13)` plus the matching `CUDA DLLs` asset for NVIDIA
     GPU offload.
   - `Windows x64 (Vulkan)` for Vulkan-capable GPU setups.
3. Extract the zip into `%USERPROFILE%\Models\qwen`.
4. Confirm that `%USERPROFILE%\Models\qwen\llama-server.exe` exists.
5. Download `qwen2.5-coder-7b-instruct-q4_k_m.gguf` from the Qwen Hugging Face
   model page into the same directory. The `huggingface-cli download` command
   above is preferred because it can resume large downloads.

Source build path, useful when no binary matches the machine:

```bash
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
cmake -B build
cmake --build build -j --target llama-server llama-cli
```

Then copy the built `llama-server` binary into `$HOME/Models/qwen` on Linux/WSL
or `%USERPROFILE%\Models\qwen` on Windows, or point the start script to the
build output.

Example `%USERPROFILE%\Models\qwen\start-qwen-llama-server.ps1`:

```powershell
$root = "$env:USERPROFILE\Models\qwen"
$server = Join-Path $root "llama-server.exe"
if (-not (Test-Path $server)) {
  $server = (Get-Command llama-server -ErrorAction Stop).Source
}

& $server `
  -m "$root\qwen2.5-coder-7b-instruct-q4_k_m.gguf" `
  --alias qwen2.5-coder-7b-instruct-q4_k_m `
  --host 127.0.0.1 `
  --port 8080 `
  -c 8192 `
  -ngl 999
```

If the machine has no supported GPU, remove or lower `-ngl`. Keep the server
listening on `127.0.0.1:8080`; the API path is `http://127.0.0.1:8080/v1`.

If you use another GGUF file, keep `--alias`, `AI_MODEL`, and `AI_QWEN_MODEL`
aligned.

Quick alternative: if `llama-server` is already installed and you do not need a
fixed local GGUF path, llama.cpp can download from Hugging Face directly:

```bash
llama-server \
  -hf Qwen/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M \
  --alias qwen2.5-coder-7b-instruct-q4_k_m \
  --host 127.0.0.1 \
  --port 8080 \
  -c 8192 \
  -ngl 999
```

PowerShell equivalent:

```powershell
llama-server `
  -hf Qwen/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M `
  --alias qwen2.5-coder-7b-instruct-q4_k_m `
  --host 127.0.0.1 `
  --port 8080 `
  -c 8192 `
  -ngl 999
```

Smoke-test the local server before starting FastOJ:

```bash
curl --noproxy '*' http://127.0.0.1:8080/v1/models
```

PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/v1/models
```

For a stronger API check:

```bash
curl --noproxy '*' http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-coder-7b-instruct-q4_k_m",
    "messages": [{"role": "user", "content": "Say OK only."}],
    "max_tokens": 8
  }'
```

PowerShell:

```powershell
$body = @{
  model = "qwen2.5-coder-7b-instruct-q4_k_m"
  messages = @(@{ role = "user"; content = "Say OK only." })
  max_tokens = 8
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8080/v1/chat/completions `
  -ContentType "application/json" `
  -Body $body
```

Daily startup from Linux/WSL uses two shells because `llama-server` stays in the
foreground.

```bash
# Shell 1
"$HOME/Models/qwen/start-qwen-llama-server.sh"
```

```bash
# Shell 2
curl --noproxy '*' http://127.0.0.1:8080/v1/models
docker compose up
```

Daily startup from PowerShell also uses two shells:

```powershell
# Shell 1
& "$env:USERPROFILE\Models\qwen\start-qwen-llama-server.ps1"
```

```powershell
# Shell 2
Invoke-RestMethod http://127.0.0.1:8080/v1/models
docker compose up
```

For detached FastOJ containers, run this in Shell 2 after the model server is
already running:

```bash
docker compose up -d
```

When FastOJ runs through Docker Compose, containers reach the host Qwen service
through `host.docker.internal`, so `.env` should contain the container-facing
URL below. The Compose file maps `host.docker.internal` to Docker's
`host-gateway` for native Linux while remaining compatible with Docker Desktop
and WSL.

```bash
AI_PROVIDER=openai_compatible
AI_BASE_URL=http://host.docker.internal:8080/v1
AI_API_KEY=sk-no-key-required
AI_MODEL=qwen2.5-coder-7b-instruct-q4_k_m

AI_QWEN_BASE_URL=http://host.docker.internal:8080/v1
AI_QWEN_API_KEY=sk-no-key-required
AI_QWEN_MODEL=qwen2.5-coder-7b-instruct-q4_k_m
```

Restart the API after changing `.env`:

```bash
docker compose up --build -d api
```

If you run the backend directly on the host instead of inside Docker, use
`http://127.0.0.1:8080/v1` for `AI_BASE_URL` and `AI_QWEN_BASE_URL`.

Stop foreground `docker compose up` with `Ctrl+C`. Stop the local Qwen service
with:

```bash
pkill -f "llama-server.*qwen2.5-coder-7b-instruct-q4_k_m" || true
```

PowerShell:

```powershell
& "$env:USERPROFILE\Models\qwen\stop-qwen-llama-server.ps1"
```

References: [Qwen GGUF quickstart](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF),
[llama.cpp releases](https://github.com/ggml-org/llama.cpp/releases), and
[llama-server docs](https://www.mintlify.com/ggml-org/llama.cpp/inference/server).

Real secrets belong in `.env` or deployment environment variables. The repository
ignores `.env` and `.env.*`; `.env.example` contains safe placeholders only.

## CI/CD Deployment

FastOJ includes GitHub Actions for pull-request checks and server deployment:

- `.github/workflows/ci.yml` runs backend lint/tests and frontend build/tests
  for pull requests and `master` pushes that include code or configuration
  changes. Documentation-only changes (`*.md`, `docs/**`, `specs/**`) are
  ignored.
- `.github/workflows/deploy.yml` builds API and worker images in GitHub
  Actions, pushes them to the configured container registry, builds the stable
  judge runtime image only when needed, then SSHes to the server as `ubuntu` to
  pull API/worker images and restart containers. Documentation-only `master`
  pushes do not trigger deployment.

Use `.env` as the runtime environment filename in both places. Locally, copy
`.env.example` to `.env`; on the server, copy `.env.prod.example` to
`/opt/projects/fastoj/.env` and edit real secrets there. A separate `.env.dev` is not
required for the normal local-plus-server workflow.

Full deployment steps are in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Safety Model

- Hidden testcase input, expected output, and actual output are never included in
  AI prompts.
- Hidden testcase content is available only through admin-only testcase and draft
  review screens.
- Normal users can explain and review only their own submissions; admins can
  access all submissions through server-side role checks.
- Public registration always creates a normal `user`; administrator accounts are
  bootstrapped from a trusted shell or managed by an existing admin.
- Password recovery is admin-assisted for now: users who forget passwords contact
  an administrator, who can set a temporary password. Password changes increment
  the user's token version so existing access and refresh tokens are rejected.
- Production judging uses Docker sandbox execution. The
  `FASTOJ_ALLOW_UNSAFE_LOCAL_EXECUTION=true` escape hatch is for local
  development only.
- Production submissions require the Redis Streams worker path. Inline judge
  fallback is limited to `DEBUG=true` or an explicit
  `JUDGE_INLINE_FALLBACK=true` local override.
- Judge workers supervise each task in a separate child process. This protects
  the worker parent from Docker API or database call hangs, while Docker remains
  the actual sandbox boundary for untrusted user code.
- In Docker Compose, the API service also mounts the Docker socket so the
  admin-only Problem Authoring Agent can sandbox-check official draft solutions
  before approval or after an admin edit/revalidation pass. Multi-language
  drafts are checked per official solution language before they can be approved.
  Dual-mode drafts can validate ACM stdin/stdout and function JSON views from
  the same logical testcase metadata.
- Sandbox containers run with network disabled, memory limits, pid limits,
  dropped capabilities, `no-new-privileges`, non-root execution, output
  truncation, timeout kill, and cleanup on the normal executor path. If the
  worker parent hard-kills a stuck judge child, the child may not reach Docker
  cleanup code, so production operations should monitor and clean residual
  `fastoj_judge_*` containers.

## Seeded Curriculum

The bundled seed data is now large enough for sustained interview practice:

- **Hot 100 interview track:** all 100 canonical Hot 100 problems, using
  original FastOJ statements and deterministic ACM input/output for linked-list,
  tree, design, and multi-answer tasks.
- **Function-mode classics:** Two Sum, Add Two Numbers, Longest Substring
  Without Repeating Characters, Valid Parentheses, Alien Dictionary, and
  Two-Car Parking Lot include starter frames, and every seeded problem now has a
  displayable, executable Python official solution.
- **Expanded deterministic cases:** seed import gives each problem at least two
  public cases plus category-sensitive hidden coverage: 30+ hidden cases for
  ordinary array/string/DP/graph/tree/list problems, 20+ for design and AI/ML
  tasks, and 15+ for high-output combination problems.
- **Localized explanations:** seed problem details include bilingual public
  sample explanations, and seeded Python official solutions expose real
  bilingual approach notes instead of generated placeholder text.
- **AI/ML algorithm exercises:** Logistic Regression Sigmoid, KNN Majority Vote,
  KMeans One Iteration, Scaled Dot-Product Attention, Softmax Cross Entropy, and
  Attention Mask Apply.

Function mode supports Python, C++, Java, JavaScript, TypeScript, Go, and selected
C wrappers for seeded function tasks. ACM mode remains available for every
problem and language. The public solution API can still be queried by the active
editor language; when that language has no official solution, it falls back to
the Python official solution and returns `language: "python"`. The judge runtime
includes Python `numpy==2.2.6` and CPU `torch==2.7.1+cpu` for AI algorithm
exercises.

## Architecture

```mermaid
flowchart LR
  Browser[React UI] --> API[FastAPI API]
  API --> DB[(PostgreSQL)]
  API --> Redis[(Redis Streams)]
  Redis --> Worker[Judge Worker]
  Worker --> Sandbox[Docker Sandbox]
  Worker --> Bus[Redis Pub/Sub]
  Bus --> API
  API --> Browser
  API --> AI[OpenAI-compatible AI Provider]
```

Key flows:

- **Run and submit:** the API persists submissions, enqueues judge work in Redis
  Streams, and returns fast status while the worker executes code in Docker.
- **Realtime feedback:** worker events are published through Redis and surfaced
  to the browser through WebSocket-first status updates, with polling fallback
  where needed.
- **Function mode:** service wrappers convert typed JSON-style function inputs
  into executable language-specific harnesses, while ACM mode keeps raw
  stdin/stdout execution available.
- **AI assistance:** the API builds prompts from public samples, verdicts, user
  code, and safe summaries. Hidden testcase content remains behind admin-only
  routes and is excluded from learner-side AI prompts.
- **Admin authoring:** draft generation, imports, validation, repair attempts,
  official solutions, and testcase review all run behind server-side role checks.

Core engineering stack:

- Backend: Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic,
  PostgreSQL, Redis Streams.
- Judge: Docker sandbox worker with async queueing, parent/child task watchdog,
  active-task markers, retries, dead-letter handling, and duplicate-task
  protection.
- Frontend: React, TypeScript, Vite, Tailwind CSS, Monaco Editor, TanStack
  Query, Zustand, Zod, xterm, Shiki, React Flow, DOMPurify, marked, and Pretext
  text measurement.
- Tooling: `uv`, `ruff`, `pytest`, `npm`, Vitest, Docker Compose, GitHub
  Actions, container registry.

## Project Layout

```text
backend/
  ai/           AI provider config, prompts, response schemas
  api/          FastAPI routes
  core/         settings, database, security, logging
  models/       SQLAlchemy models
  schemas/      Pydantic API schemas
  scripts/      seed/admin/repair utilities
  services/     business logic, judging, function wrappers
  worker/       judge worker
frontend/
  src/
    components/
    lib/
    stores/
    main.tsx
tests/          backend tests
docs/           deployment, handoff, acceptance, and project-guide notes
specs/          product and implementation planning notes
```

## Quality Gate

Run these before handing off substantial changes:

```bash
uv run ruff check .
uv run pytest
cd frontend && npm run build
cd frontend && npm test
```

When judge, worker, WebSocket/SSE, sandbox, or real submission behavior changes, also
run:

```bash
docker compose up --build -d api worker
```

The full manual acceptance checklist lives in
[`docs/ACCEPTANCE_HARNESS.md`](docs/ACCEPTANCE_HARNESS.md).

## Known Limits

- Monaco and Shiki currently ship directly in the frontend bundle, so production
  chunks are large.
- C function-mode wrappers cover only simpler seeded signatures today; use ACM
  mode for C on matrix/string-heavy AI tasks until those wrappers are expanded.
- MLE classification depends on Docker runtime exit behavior.
- AI quality depends on the configured OpenAI-compatible model and prompt
  behavior.
- The initial Alembic migration is a baseline for the current schema and should
  be validated against any existing production database before rollout.
