# FastOJ Dependency Audit

Date: 2026-05-12

## Toolchain

| Tool | Version | Result |
| --- | --- | --- |
| Python | 3.12.10 | OK, satisfies Python 3.11+ |
| uv | 0.10.2 | OK |
| Node.js | v24.15.0 | OK |
| npm | 11.12.1 | OK |
| Docker | 29.2.1 | OK |
| Docker Compose | v5.1.0 | OK |

## Repository Inputs Checked

- `pyproject.toml`: present.
- `uv.lock`: present.
- `docker-compose.yml`: present.
- `Dockerfile.api`: present.
- `Dockerfile.judge`: present.
- `frontend/`: present.
- Existing frontend package manifest: none before audit.
- Existing frontend lockfile: none before audit.

## Backend Dependencies

No backend dependencies were added during Phase 0. Existing pinned dependencies from `pyproject.toml` were reused.

Validation command:

```bash
uv sync
```

Result: passed. Initial sandboxed execution could not access the user-level uv cache at `C:\Users\Lightning\AppData\Local\uv\cache`; the command passed when rerun with the approved `uv sync` permission.

## Frontend Dependencies

Package manager: npm. `npm config set save-exact true` was executed before installing dependencies.

Production dependencies installed:

- `react@19.2.6`
- `react-dom@19.2.6`
- `@vitejs/plugin-react@6.0.1`
- `vite@8.0.12`
- `typescript@6.0.3`
- `tailwindcss@4.3.0`
- `postcss@8.5.14`
- `autoprefixer@10.5.0`
- `monaco-editor@0.55.1`
- `@tanstack/react-query@5.100.10`
- `zustand@5.0.13`
- `zod@4.4.3`
- `@xterm/xterm@6.0.0`
- `@xterm/addon-fit@0.11.0`
- `shiki@4.0.2`
- `@xyflow/react@12.10.2`
- `@chenglou/pretext@0.0.7`

Development and test dependencies installed:

- `vitest@4.1.6`
- `@testing-library/react@16.3.2`
- `@testing-library/jest-dom@6.9.1`
- `@testing-library/user-event@14.6.1`
- `jsdom@29.1.1`
- `eslint@10.3.0`
- `@eslint/js@10.0.1`
- `typescript-eslint@8.59.3`
- `eslint-plugin-react-hooks@7.1.1`
- `@types/node@25.7.0`
- `@types/react@19.2.14`
- `@types/react-dom@19.2.3`
- `@tailwindcss/postcss@4.3.0`

`@tailwindcss/postcss` was added because Tailwind CSS 4 no longer exposes the PostCSS plugin through the `tailwindcss` package directly.

## Installation Commands

```bash
cd frontend
npm config set save-exact true
npm install react react-dom @vitejs/plugin-react vite typescript tailwindcss postcss autoprefixer monaco-editor @tanstack/react-query zustand zod @xterm/xterm @xterm/addon-fit shiki @xyflow/react @chenglou/pretext
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom eslint @eslint/js typescript-eslint eslint-plugin-react-hooks
npm install -D @types/node @types/react @types/react-dom
npm install -D @tailwindcss/postcss
```

## Initial Verification

| Command | Result |
| --- | --- |
| `uv sync` | Passed |
| `cd frontend && npm install` | Passed |
| `cd frontend && npm run build` | Passed |
| `cd frontend && npm test` | Passed |

Notes:

- Vite/Vitest on Windows needed permission to spawn helper processes outside the default sandbox during verification.
- `npm install` reported 2 moderate vulnerabilities. `npm audit fix --force` was not applied because it may introduce breaking dependency changes; this remains tracked as a dependency risk.
