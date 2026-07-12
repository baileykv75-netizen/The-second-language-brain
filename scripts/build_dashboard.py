from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {"inbox", "templates", "indexes", ".git", "scripts"}


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


def rel(path: Path, root: Path = ROOT) -> str:
    return path.relative_to(root).as_posix()


def link(path: str, label: str) -> str:
    return f"[{label}]({path})"


def node_link(path: Path, meta: dict) -> str:
    return f"[{meta.get('title', path.stem)}]({rel(path)})"


def first_existing(paths: list[Path]) -> str:
    for path in paths:
        if path.exists():
            return rel(path)
    return ""


def latest_due_file(root: Path) -> Path | None:
    files = sorted((root / "Review_System" / "due").glob("*.md"), reverse=True)
    return files[0] if files else None


def collect_by_type(nodes: list[tuple[Path, dict]], node_type: str, limit: int = 8) -> list[str]:
    matches = [(path, meta) for path, meta in nodes if meta.get("type") == node_type]
    matches.sort(key=lambda item: str(item[1].get("created", "")), reverse=True)
    return [f"- {node_link(path, meta)}" for path, meta in matches[:limit]]


def collect_index_links(root: Path, prefix: str, limit: int = 12) -> list[str]:
    rows = []
    for path in sorted((root / "indexes").glob(f"{prefix}_*.md"))[:limit]:
        label = path.stem.replace(f"{prefix}_", "").replace("_", " ").title()
        rows.append(f"- [{label}]({rel(path)})")
    return rows


def build(root: Path = ROOT) -> None:
    nodes = iter_nodes(root)
    due_file = latest_due_file(root)
    session_count = sum(1 for _, meta in nodes if meta.get("type") == "session")
    vocab_count = sum(1 for _, meta in nodes if meta.get("type") == "vocabulary")
    mistake_count = sum(1 for _, meta in nodes if meta.get("type") == "grammar_error")
    expression_count = sum(1 for _, meta in nodes if meta.get("type") == "expression")
    response_count = sum(1 for _, meta in nodes if meta.get("type") == "mini_response")
    story_count = sum(1 for _, meta in nodes if meta.get("type") == "personal_story")

    today_review = rel(due_file) if due_file else "Review_System/due/"
    latest_sessions = collect_by_type(nodes, "session", 5)
    vocab_rows = collect_by_type(nodes, "vocabulary", 8)
    mistake_rows = collect_by_type(nodes, "grammar_error", 5)
    expression_rows = collect_by_type(nodes, "expression", 5)
    response_rows = collect_by_type(nodes, "mini_response", 5)
    story_rows = collect_by_type(nodes, "personal_story", 5)
    topic_rows = collect_index_links(root, "topic", 12)
    skill_rows = collect_index_links(root, "skill", 8)

    lines = [
        "# The Second Language Brain",
        "",
        "A personal IELTS Speaking knowledge tree. Open this page like a learning app: review first, then browse topics, skills, vocabulary, mini responses, expressions, and sessions.",
        "",
        "## Start Here",
        "",
        "- Mobile app view: [GitHub Pages](https://baileykv75-netizen.github.io/The-second-language-brain/)",
        f"- Today's review: [{Path(today_review).stem if due_file else 'Review folder'}]({today_review})",
        "- Add a new structured session: [inbox/](inbox/)",
        "- Session template: [templates/session_template.md](templates/session_template.md)",
        "- Full session history: [indexes/sessions.md](indexes/sessions.md)",
        "",
        "## Quick Stats",
        "",
        f"- Sessions: {session_count}",
        f"- Vocabulary nodes: {vocab_count}",
        f"- Grammar mistakes: {mistake_count}",
        f"- Expressions: {expression_count}",
        f"- Mini responses: {response_count}",
        f"- Personal stories: {story_count}",
        "",
        "## Main Entrances",
        "",
        "| Area | Open |",
        "| --- | --- |",
        f"| Review | {link(today_review, 'Due list')} |",
        f"| Topics | {link('IELTS_Topics/', 'Topic tree')} |",
        f"| Skills | {link('Skill_Tree/', 'Skill tree')} |",
        f"| Vocabulary | {link('indexes/vocabulary.md', 'Vocabulary index')} |",
        f"| Grammar mistakes | {link('indexes/mistakes.md', 'Mistake log')} |",
        f"| Expressions | {link('indexes/expressions.md', 'Expression bank')} |",
        f"| Mini responses | {link('indexes/responses.md', 'Response bank')} |",
        f"| Personal stories | {link('indexes/personal_stories.md', 'Story bank')} |",
        "",
        "## Latest Sessions",
        "",
        *(latest_sessions or ["- No sessions yet."]),
        "",
        "## Topic Tree",
        "",
        *(topic_rows or ["- No topic indexes yet."]),
        "",
        "## Speaking Skill Tree",
        "",
        *(skill_rows or ["- No skill indexes yet."]),
        "",
        "## Recent Vocabulary",
        "",
        *(vocab_rows or ["- No vocabulary nodes yet."]),
        "",
        "## Recent Grammar Mistakes",
        "",
        *(mistake_rows or ["- No grammar mistakes yet."]),
        "",
        "## Expression Bank",
        "",
        *(expression_rows or ["- No expressions yet."]),
        "",
        "## Mini Response Bank",
        "",
        *(response_rows or ["- No mini responses yet."]),
        "",
        "## Personal Stories",
        "",
        *(story_rows or ["- No personal stories yet."]),
        "",
        "## How To Update This Brain",
        "",
        "For GPT/Codex web workflow, paste a structured IELTS session summary and ask Codex to update this repository:",
        "",
        "```text",
        "Use GitHub repo baileykv75-netizen/The-second-language-brain.",
        "Please add this IELTS session to the knowledge tree, run the pipeline, commit, and push to main.",
        "",
        "[paste structured session summary]",
        "```",
        "",
        "For local Windows workflow:",
        "",
        "```powershell",
        "powershell -ExecutionPolicy Bypass -File .\\scripts\\run_pipeline.ps1 inbox\\2026-07-12_AI_Game_Ideas.md",
        "```",
        "",
        "## Content Rules",
        "",
        "- English is used for model answers, examples, expressions, and speaking output.",
        "- Chinese is used for grammar explanations, review notes, and learning guidance.",
        "- The scripts organize and link your material. They do not rewrite your personal ideas.",
        "",
        f"_Dashboard last generated: {date.today().isoformat()}_",
    ]

    (root / "README.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print("Wrote dashboard: README.md")


def main(argv: list[str]) -> int:
    build(ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
