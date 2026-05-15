from __future__ import annotations

import argparse
import getpass
import os
import sys

from sqlalchemy.orm import Session

from backend.core.database import SessionLocal
from backend.core.security import get_password_hash
from backend.models import User

MIN_ADMIN_PASSWORD_LENGTH = 12
DEFAULT_PASSWORD_ENV = "FASTOJ_ADMIN_PASSWORD"


def validate_admin_password(password: str) -> None:
    if len(password) < MIN_ADMIN_PASSWORD_LENGTH:
        raise ValueError(f"Admin password must be at least {MIN_ADMIN_PASSWORD_LENGTH} characters long.")
    if password.strip() != password or not password.strip():
        raise ValueError("Admin password must not be empty or start/end with whitespace.")


def create_or_promote_admin(
    db: Session,
    *,
    username: str,
    email: str,
    password: str | None,
    reset_password: bool = False,
) -> tuple[User, str]:
    matches = db.query(User).filter((User.username == username) | (User.email == email)).all()
    unique_matches = {user.id: user for user in matches}
    if len(unique_matches) > 1:
        raise ValueError("Username and email already belong to different users.")

    existing = next(iter(unique_matches.values()), None)
    if existing:
        if existing.username != username or existing.email != email:
            raise ValueError("Existing user must match both username and email before promotion.")

        action = "already_admin" if existing.role == "admin" and existing.is_active else "promoted"
        existing.role = "admin"
        existing.is_active = True
        if reset_password:
            if password is None:
                raise ValueError("Password is required when --reset-password is used.")
            validate_admin_password(password)
            existing.password_hash = get_password_hash(password)
            action = "updated_password"
        db.commit()
        db.refresh(existing)
        return existing, action

    if password is None:
        raise ValueError("Password is required when creating a new admin user.")
    validate_admin_password(password)
    user = User(
        username=username,
        email=email,
        password_hash=get_password_hash(password),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, "created"


def _read_password(*, password_arg: str | None, password_env: str, required: bool) -> str | None:
    if password_arg:
        return password_arg

    env_password = os.getenv(password_env)
    if env_password:
        return env_password

    if not required:
        return None

    password = getpass.getpass("Admin password: ")
    confirm = getpass.getpass("Confirm admin password: ")
    if password != confirm:
        raise ValueError("Passwords do not match.")
    return password


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or promote a FastOJ administrator account.",
    )
    parser.add_argument("--username", required=True, help="Admin username.")
    parser.add_argument("--email", required=True, help="Admin email address.")
    parser.add_argument(
        "--password",
        help="Admin password. Prefer an interactive prompt or FASTOJ_ADMIN_PASSWORD in shared shells.",
    )
    parser.add_argument(
        "--password-env",
        default=DEFAULT_PASSWORD_ENV,
        help=f"Environment variable to read the password from. Default: {DEFAULT_PASSWORD_ENV}.",
    )
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="Reset the password if the user already exists.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    db = SessionLocal()
    try:
        existing = db.query(User).filter((User.username == args.username) | (User.email == args.email)).first()
        password = _read_password(
            password_arg=args.password,
            password_env=args.password_env,
            required=existing is None or args.reset_password,
        )
        user, action = create_or_promote_admin(
            db,
            username=args.username,
            email=args.email,
            password=password,
            reset_password=args.reset_password,
        )
    except Exception as exc:
        db.rollback()
        print(f"Failed to create admin: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    print(f"Admin {action}: username={user.username} email={user.email} role={user.role}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
