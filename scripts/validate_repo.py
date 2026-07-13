from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NODE_DIRS = {
    "Daily_Sessions",
    "Skill_Tree/Vocabulary",
    "Skill_Tree/Pronunciation",
    "Mistake_Log",
    "Expression_Bank",
    "Response_Bank",
    "Personal_Stories",
}
REQUIRED_FIELDS = ["id", "type", "title", "created", "source_session", "topics", "skills", "related"]
REQUIRED_REVIEW_FIELDS = ["status", "next_due", "interval_days"]
STAT_LABELS = {
    "Sessions": "sessions",
    "Vocabulary nodes": "vocabulary",
    "Grammar mistakes": "grammarMistakes",
    "Expressions": "expressions",
    "Mini responses": "responses",
    "Personal stories": "stories",
}


def parse_list(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return [item.strip().strip("\"'") for item in value.split(",") if item.strip()]


def parse_frontmatter(text: str) -> tuple[dict, str, bool]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not match:
        return {}, text, False
    meta: dict[str, object] = {}
    current_parent = None
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if line.startswith("  ") and current_parent:
            if ":" not in line:
                continue
            key, raw = line.strip().split(":", 1)
            parent = meta.setdefault(current_parent, {})
            if isinstance(parent, dict):
                parent[key.strip()] = raw.strip().strip("\"'")
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
    return meta, text[match.end():], True


def is_node_path(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    return rel.parts and "/".join(rel.parts[:2]) in NODE_DIRS or rel.parts[:1] and rel.parts[0] in NODE_DIRS


def iter_node_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.md") if path.name.lower() != "readme.md" and is_node_path(path, root))


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def valid_date(value: object) -> bool:
    try:
        datetime.strptime(str(value), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def count_nodes(nodes: list[tuple[Path, dict]]) -> dict[str, int]:
    return {
        "sessions": sum(1 for _, meta in nodes if meta.get("type") == "session"),
        "vocabulary": sum(1 for _, meta in nodes if meta.get("type") == "vocabulary"),
        "grammarMistakes": sum(1 for _, meta in nodes if meta.get("type") == "grammar_error"),
        "expressions": sum(1 for _, meta in nodes if meta.get("type") == "expression"),
        "responses": sum(1 for _, meta in nodes if meta.get("type") == "mini_response"),
        "stories": sum(1 for _, meta in nodes if meta.get("type") == "personal_story"),
    }


def validate_links(root: Path, errors: list[str]) -> None:
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for directory in [root / "indexes", root / "IELTS_Topics"]:
        if not directory.exists():
            continue
        for path in directory.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            for target in link_pattern.findall(text):
                if target.startswith(("http://", "https://", "#")):
                    continue
                clean_target = target.split("#", 1)[0]
                resolved = (path.parent / clean_target).resolve()
                if not resolved.exists():
                    errors.append(f"{rel(path, root)} links to missing file: {target}")


def validate_readme_stats(root: Path, counts: dict[str, int], errors: list[str]) -> None:
    readme = root / "README.md"
    if not readme.exists():
        errors.append("README.md is missing.")
        return
    text = readme.read_text(encoding="utf-8")
    for label, key in STAT_LABELS.items():
        match = re.search(rf"^- {re.escape(label)}:\s*(\d+)\s*$", text, re.M)
        if not match:
            errors.append(f"README Quick Stats missing: {label}")
            continue
        if int(match.group(1)) != counts[key]:
            errors.append(f"README Quick Stats mismatch for {label}: {match.group(1)} != {counts[key]}")


def validate_docs_stats(root: Path, counts: dict[str, int], total: int, errors: list[str]) -> None:
    data_path = root / "docs" / "data.json"
    if not data_path.exists():
        errors.append("docs/data.json is missing.")
        return
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    stats = payload.get("stats", {})
    expected = dict(counts)
    expected["total"] = total
    for key, value in expected.items():
        if stats.get(key) != value:
            errors.append(f"docs/data.json stats mismatch for {key}: {stats.get(key)} != {value}")


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    nodes: list[tuple[Path, dict]] = []

    for path in iter_node_files(root):
        meta, _, has_frontmatter = parse_frontmatter(path.read_text(encoding="utf-8"))
        if not has_frontmatter:
            errors.append(f"{rel(path, root)} is missing YAML front matter.")
            continue
        nodes.append((path, meta))
        for key in REQUIRED_FIELDS:
            if key not in meta:
                errors.append(f"{rel(path, root)} is missing required field: {key}")
        review = meta.get("review")
        if not isinstance(review, dict):
            errors.append(f"{rel(path, root)} is missing review metadata.")
            continue
        for key in REQUIRED_REVIEW_FIELDS:
            if key not in review:
                errors.append(f"{rel(path, root)} is missing review.{key}")
        if "next_due" in review and not valid_date(review["next_due"]):
            errors.append(f"{rel(path, root)} has invalid review.next_due: {review['next_due']}")
        if "created" in meta and not valid_date(meta["created"]):
            errors.append(f"{rel(path, root)} has invalid created date: {meta['created']}")

    ids = [str(meta.get("id")) for _, meta in nodes if meta.get("id")]
    for node_id, count in Counter(ids).items():
        if count > 1:
            errors.append(f"Duplicate node id: {node_id}")

    session_ids = {str(meta.get("id")) for _, meta in nodes if meta.get("type") == "session"}
    for path, meta in nodes:
        source_session = str(meta.get("source_session", ""))
        if meta.get("type") == "session":
            if source_session != meta.get("id"):
                errors.append(f"{rel(path, root)} session source_session must equal id.")
        elif source_session not in session_ids:
            errors.append(f"{rel(path, root)} source_session does not point to a session: {source_session}")

    validate_links(root, errors)
    counts = count_nodes(nodes)
    validate_readme_stats(root, counts, errors)
    validate_docs_stats(root, counts, len(nodes), errors)
    return errors


def main(argv: list[str]) -> int:
    errors = validate(ROOT)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
