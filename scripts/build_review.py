from __future__ import annotations

import re
import sys
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {"inbox", "templates", "indexes", ".git"}


def parse_list(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return [item.strip().strip("\"'") for item in value.split(",") if item.strip()]


def parse_frontmatter(text: str) -> dict:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not match:
        return {}
    meta: dict[str, object] = {}
    current_parent = None
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if line.startswith("  ") and current_parent:
            key, raw = line.strip().split(":", 1)
            parent = meta.setdefault(current_parent, {})
            if isinstance(parent, dict):
                parent[key.strip()] = raw.strip()
            continue
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        raw = raw.strip()
        current_parent = key if raw == "" else None
        if raw.startswith("[") and raw.endswith("]"):
            meta[key] = parse_list(raw)
        elif raw:
            meta[key] = raw.strip("\"'")
        else:
            meta[key] = {}
    return meta


def iter_nodes(root: Path) -> list[tuple[Path, dict]]:
    nodes: list[tuple[Path, dict]] = []
    for path in root.rglob("*.md"):
        parts = set(path.relative_to(root).parts)
        if parts & SKIP_DIRS:
            continue
        meta = parse_frontmatter(path.read_text(encoding="utf-8"))
        if meta.get("id") and meta.get("type"):
            nodes.append((path, meta))
    return sorted(nodes, key=lambda item: str(item[0]))


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def build(root: Path = ROOT, review_date: date | None = None) -> None:
    review_date = review_date or date.today()
    due_rows: list[str] = []
    upcoming_rows: list[str] = []

    for path, meta in iter_nodes(root):
        review = meta.get("review", {})
        if not isinstance(review, dict):
            continue
        raw_due = review.get("next_due")
        if not raw_due:
            continue
        due_date = datetime.strptime(str(raw_due), "%Y-%m-%d").date()
        row = f"- [{meta.get('title', path.stem)}](../../{rel(path, root)}) - `{meta.get('type')}` - due `{due_date.isoformat()}`"
        if due_date <= review_date:
            due_rows.append(row)
        else:
            upcoming_rows.append(row)

    output = [
        f"# Review Due: {review_date.isoformat()}",
        "",
        "## Due Now",
        "",
        *(due_rows or ["No items due yet."]),
        "",
        "## Upcoming",
        "",
        *(upcoming_rows[:50] or ["No upcoming items yet."]),
    ]
    out_path = root / "Review_System" / "due" / f"{review_date.isoformat()}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
    print(f"Wrote review list: {out_path.relative_to(root)}")


def main(argv: list[str]) -> int:
    review_date = date.today()
    if len(argv) == 2:
        review_date = datetime.strptime(argv[1], "%Y-%m-%d").date()
    build(ROOT, review_date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
