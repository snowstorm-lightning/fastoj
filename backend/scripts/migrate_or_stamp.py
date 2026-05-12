from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from backend.core.database import engine

logger = logging.getLogger(__name__)


def _alembic_config() -> Config:
    repo_root = Path(__file__).resolve().parents[2]
    return Config(str(repo_root / "backend" / "alembic.ini"))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    config = _alembic_config()

    with engine.connect() as connection:
        inspector = inspect(connection)
        table_names = set(inspector.get_table_names())

    has_alembic_version = "alembic_version" in table_names
    has_existing_schema = bool({"users", "problems", "submissions"} & table_names)

    if has_existing_schema and not has_alembic_version:
        logger.info("Existing FastOJ schema detected without Alembic metadata; stamping baseline revision.")
        command.stamp(config, "head")

    command.upgrade(config, "head")


if __name__ == "__main__":
    main()
