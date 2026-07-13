from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import build_dashboard
import build_indexes
import build_review
import build_site
import process_session
import validate_repo


ROOT = Path(__file__).resolve().parents[1]


def resolve_input(raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        raise FileNotFoundError(f"Session input not found: {path}")
    return path


def run(input_path: Path) -> int:
    today = date.today()
    print(f"Pipeline date: {today.isoformat()}")
    print(f"Input: {input_path.relative_to(ROOT)}")

    session_path = process_session.process(input_path)
    build_indexes.build(ROOT)
    build_review.build(ROOT, today)
    build_dashboard.build(ROOT, today)
    build_site.build(ROOT)
    errors = validate_repo.validate(ROOT)
    if errors:
        print("")
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("")
    print("Pipeline complete.")
    print(f"- Session: {session_path.relative_to(ROOT)}")
    print(f"- Review: Review_System/due/{today.isoformat()}.md")
    print("- Website data: docs/data.json")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python scripts/run_pipeline.py inbox/<session-file>.md")
        return 2
    try:
        return run(resolve_input(argv[1]))
    except Exception as exc:
        print(f"Pipeline failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
