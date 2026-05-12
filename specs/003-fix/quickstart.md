# Quickstart: Fix WSL移植 Issues

## Prerequisites

- Windows 10/11 with WSL removed or bypassed
- Python 3.11+ installed
- uv package manager installed

## Cleanup Steps

### 1. Remove Linux Cache Directories

```powershell
# Remove .venv (Linux virtual environment)
Remove-Item -Recurse -Force .venv

# Remove all __pycache__ directories
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# Remove cache directories
Remove-Item -Recurse -Force .ruff_cache
Remove-Item -Recurse -Force .pytest_cache
```

Or using bash in the project directory:

```bash
rm -rf .venv
find . -type d -name "__pycache__" -exec rm -rf {} +
rm -rf .ruff_cache .pytest_cache
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Verify Project Works

```bash
# Run linter
ruff check .

# Run tests
pytest

# Start API server (optional)
cd backend && uvicorn main:app --reload
```

## Troubleshooting

- If import errors occur, ensure `.env` file exists and database/redis are accessible
- For Docker services: `docker-compose up -d postgres redis`
