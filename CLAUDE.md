# fastoj Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-16

## Active Technologies
- Python 3.11+ (from pyproject.toml requires-python = ">=3.11") + FastAPI, SQLAlchemy 2.0, Pydantic, Redis, Python Docker SDK (002-docs-uv-align)
- PostgreSQL 14+ (constitution requirement) (002-docs-uv-align)
- Python 3.11+ (from pyproject.toml `requires-python = ">=3.11"`) + FastAPI, SQLAlchemy 2.0, Pydantic, Redis, Python Docker SDK (002-docs-uv-align)
- PostgreSQL (via SQLAlchemy with asyncpg/psycopg2) (002-docs-uv-align)
- Python 3.11+ (from pyproject.toml) + FastAPI, SQLAlchemy 2.0, Pydantic, Redis, Python Docker SDK (003-fix)
- PostgreSQL (via Docker) (003-fix)

- Python 3.11+ + FastAPI, SQLAlchemy, Pydantic, Redis, Python Docker SDK (001-oj-product-requirements)

## Project Structure

```text
backend/
├── api/           # FastAPI routes (modular by domain)
├── core/          # Core configuration
├── models/        # SQLAlchemy models
├── schemas/       # Pydantic schemas
├── services/      # Business logic
├── worker/        # Judge worker
├── sandbox/       # Docker sandbox
└── scripts/       # Utility scripts
tests/
```

## Commands

```bash
uv sync          # Install dependencies
pytest           # Run tests
ruff check .     # Lint code
```

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 003-fix: Added Python 3.11+ (from pyproject.toml) + FastAPI, SQLAlchemy 2.0, Pydantic, Redis, Python Docker SDK
- 002-docs-uv-align: Added Python 3.11+ (from pyproject.toml `requires-python = ">=3.11"`) + FastAPI, SQLAlchemy 2.0, Pydantic, Redis, Python Docker SDK
- 002-docs-uv-align: Added Python 3.11+ (from pyproject.toml requires-python = ">=3.11") + FastAPI, SQLAlchemy 2.0, Pydantic, Redis, Python Docker SDK


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
