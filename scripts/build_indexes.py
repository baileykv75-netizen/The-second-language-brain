from __future__ import annotations

import re
import sys
from collections import defaultdict
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


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "item"


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


def write_index(path: Path, title: str, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = [f"# {title}", ""]
    body.extend(rows or ["No entries yet."])
    path.write_text("\n".join(body).rstrip() + "\n", encoding="utf-8")


def link_row(path: Path, meta: dict, root: Path) -> str:
    title = meta.get("title", path.stem)
    node_type = meta.get("type", "node")
    return f"- [{title}](../{rel(path, root)}) - `{node_type}`"


def build(root: Path = ROOT) -> None:
    nodes = iter_nodes(root)
    by_type: dict[str, list[str]] = defaultdict(list)
    by_topic: dict[str, list[str]] = defaultdict(list)
    by_skill: dict[str, list[str]] = defaultdict(list)

    for path, meta in nodes:
        by_type[str(meta.get("type"))].append(link_row(path, meta, root))
        for topic in meta.get("topics", []) if isinstance(meta.get("topics"), list) else []:
            by_topic[topic].append(link_row(path, meta, root))
        for skill in meta.get("skills", []) if isinstance(meta.get("skills"), list) else []:
            by_skill[skill].append(link_row(path, meta, root))

    write_index(root / "indexes" / "sessions.md", "Sessions", by_type.get("session", []))
    write_index(root / "indexes" / "vocabulary.md", "Vocabulary Index", by_type.get("vocabulary", []))
    write_index(root / "indexes" / "mistakes.md", "Grammar Mistake Index", by_type.get("grammar_error", []))
    write_index(root / "indexes" / "expressions.md", "Expression Bank Index", by_type.get("expression", []))
    write_index(root / "indexes" / "personal_stories.md", "Personal Story Index", by_type.get("personal_story", []))

    for topic, rows in sorted(by_topic.items()):
        write_index(root / "indexes" / f"topic_{slugify(topic)}.md", f"Topic: {topic}", rows)
        write_index(root / "IELTS_Topics" / f"{slugify(topic)}.md", f"IELTS Topic: {topic}", rows)

    for skill, rows in sorted(by_skill.items()):
        write_index(root / "indexes" / f"skill_{slugify(skill)}.md", f"Speaking Skill: {skill}", rows)
        write_index(root / "Skill_Tree" / "Speaking_Skills" / f"{slugify(skill)}.md", f"Speaking Skill: {skill}", rows)

    print(f"Indexed {len(nodes)} knowledge nodes.")


def main(argv: list[str]) -> int:
    build(ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
