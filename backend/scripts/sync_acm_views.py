#!/usr/bin/env python3
"""Backfill ACM testcase metadata for existing function-mode problems."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass

from backend.core.database import SessionLocal
from backend.models import Problem, TestCase
from backend.scripts.seed_testcase_augmentation import function_case_io_metadata
from backend.services.problem_modes import FUNCTION_SIGNATURES


@dataclass
class Stats:
    visited: int = 0
    updated: int = 0
    upgraded: int = 0
    failed: int = 0


def _parse_json(value: str | None) -> dict:
    if not value:
        return {}
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _problem_signature(problem: Problem) -> str | None:
    return problem.function_signature or FUNCTION_SIGNATURES.get(str(problem.slug))


def _can_promote_to_both(problem: Problem, problems_total: int, completed: int) -> bool:
    if problem.mode != "function":
        return False
    return problems_total > 0 and completed == problems_total


def backfill_acm_views(dry_run: bool = False) -> Stats:
    """Populate missing test case io_metadata.acm for function-mode problems."""
    db = SessionLocal()
    stats = Stats()
    try:
        problems = (
            db.query(Problem)
            .filter(Problem.is_public.is_(True))
            .order_by(Problem.created_at.asc())
            .all()
        )
        for problem in problems:
            if _problem_signature(problem) is None:
                continue
            if str(problem.mode or "").lower() not in {"function", "both"}:
                continue

            slug = str(problem.slug)
            testcase_candidates = (
                db.query(TestCase)
                .filter(TestCase.problem_id == problem.id)
                .order_by(TestCase.order.asc(), TestCase.created_at.asc())
                .all()
            )
            if not testcase_candidates:
                continue

            stats.visited += 1
            completed = 0
            changed = False

            for testcase in testcase_candidates:
                metadata = _parse_json(getattr(testcase, "io_metadata_json", None))

                views = function_case_io_metadata(slug, str(testcase.input), str(testcase.output))
                if not views:
                    if metadata.get("acm") and metadata.get("function"):
                        completed += 1
                        continue
                    stats.failed += 1
                    continue

                if not metadata:
                    metadata = views
                else:
                    metadata["function"] = views.get("function", {})
                    metadata["acm"] = views.get("acm", {})

                if not metadata.get("acm") or not metadata.get("function"):
                    stats.failed += 1
                    continue

                next_metadata = json.dumps(metadata, separators=(",", ":"))
                if testcase.io_metadata_json != next_metadata:
                    testcase.io_metadata_json = next_metadata
                    changed = True
                completed += 1

            if _can_promote_to_both(problem, len(testcase_candidates), completed):
                problem.mode = "both"
                changed = True
                stats.upgraded += 1

            if changed and not dry_run:
                stats.updated += 1
        if not dry_run:
            db.commit()
    finally:
        db.close()
    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Report what would be updated without writing DB changes.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stats = backfill_acm_views(dry_run=args.dry_run)
    print(
        f"visited={stats.visited} upgraded={stats.upgraded} "
        f"updated={stats.updated} failed={stats.failed} dry_run={args.dry_run}"
    )


if __name__ == "__main__":
    main()
