from __future__ import annotations

import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    from normalize_session_update import normalize_text
except ImportError:  # pragma: no cover - keeps direct imports tolerant.
    normalize_text = None


ROOT = Path(__file__).resolve().parents[1]
REVIEW_INTERVALS = [1, 3, 7, 14, 30]
NODE_DIRS = [
    "Daily_Sessions",
    "Skill_Tree/Vocabulary",
    "Skill_Tree/Pronunciation",
    "Mistake_Log",
    "Expression_Bank",
    "Response_Bank",
    "Personal_Stories",
]


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "item"


def parse_list(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return [item.strip().strip("\"'") for item in value.split(",") if item.strip()]


def unique_list(items: list[str]) -> list[str]:
    seen = set()
    values = []
    for item in items:
        normalized = item.strip()
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            values.append(normalized)
    return values


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not match:
        return {}, text
    meta: dict[str, object] = {}
    current_parent = None
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if line.startswith("  ") and current_parent:
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
    return meta, text[match.end():]


def yaml_value(value) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(str(item) for item in value) + "]"
    return str(value)


def frontmatter(meta: dict) -> str:
    lines = ["---"]
    for key, value in meta.items():
        if key == "review" and isinstance(value, dict):
            lines.append("review:")
            for review_key, review_value in value.items():
                lines.append(f"  {review_key}: {yaml_value(review_value)}")
        else:
            lines.append(f"{key}: {yaml_value(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def split_sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.M))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        title = re.sub(r"^\d+\.\s*", "", match.group(1).strip()).lower()
        sections[title] = text[start:end].strip()
    return sections


def h3_blocks(section: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^###\s+(.+?)\s*$", section, re.M))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(section)
        blocks.append((match.group(1).strip(), section[start:end].strip()))
    return blocks


def field(block: str, label: str) -> str:
    pattern = re.compile(
        rf"^{re.escape(label)}:\s*(?:\n(.*?))?(?=^[A-Z][A-Za-z ]+:\s*$|^[A-Z][A-Za-z ]+:\s+|\Z)",
        re.M | re.S,
    )
    match = pattern.search(block)
    if not match:
        inline = re.search(rf"^{re.escape(label)}:\s*(.+)$", block, re.M)
        return inline.group(1).strip() if inline else ""
    return (match.group(1) or "").strip()


def find_section(sections: dict[str, str], keyword: str) -> str:
    for title, body in sections.items():
        if keyword in title:
            return body
    return ""


def find_any_section(sections: dict[str, str], keywords: list[str]) -> str:
    for keyword in keywords:
        body = find_section(sections, keyword)
        if body:
            return body
    return ""


def write_node(path: Path, meta: dict, body: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = frontmatter(meta) + body.strip() + "\n"
    action = "updated" if path.exists() else "created"
    path.write_text(content, encoding="utf-8")
    return action


def session_date(input_path: Path, meta: dict) -> date:
    raw = str(meta.get("date") or meta.get("created") or "")
    if raw:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    match = re.search(r"(\d{4}-\d{2}-\d{2})", input_path.name)
    if match:
        return datetime.strptime(match.group(1), "%Y-%m-%d").date()
    return date.today()


def normalize_meta_list(meta: dict, key: str) -> list[str]:
    value = meta.get(key, [])
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return parse_list(value)
    return []


def base_node_meta(
    node_id: str,
    node_type: str,
    title: str,
    created: date,
    source_session: str,
    topics: list[str],
    skills: list[str],
    related: list[str],
) -> dict:
    return {
        "id": node_id,
        "type": node_type,
        "title": title,
        "created": created.isoformat(),
        "source_session": source_session,
        "topics": unique_list(topics),
        "skills": unique_list(skills),
        "related": unique_list(related),
        "review": {
            "status": "new",
            "next_due": (created + timedelta(days=REVIEW_INTERVALS[0])).isoformat(),
            "interval_days": REVIEW_INTERVALS[0],
        },
    }


def node_key(created: date, session_slug: str, item_slug: str) -> str:
    return f"{created.strftime('%Y%m%d')}_{session_slug}_{item_slug}"


def cleanup_session_nodes(source_session: str, keep_paths: set[Path]) -> list[Path]:
    removed: list[Path] = []
    normalized_keep = {path.resolve() for path in keep_paths}
    for directory in NODE_DIRS:
        root = ROOT / directory
        if not root.exists():
            continue
        for path in root.glob("*.md"):
            if path.resolve() in normalized_keep:
                continue
            meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
            if meta.get("source_session") == source_session:
                path.unlink()
                removed.append(path)
    return removed


def process(input_path: Path) -> Path:
    raw_text = input_path.read_text(encoding="utf-8")
    if normalize_text:
        raw_text = normalize_text(raw_text, input_path)
    meta, body = parse_frontmatter(raw_text)
    created = session_date(input_path, meta)
    title = str(meta.get("title") or input_path.stem)
    session_slug = slugify(title)
    source_session = f"session_{created.strftime('%Y%m%d')}_{session_slug}"
    topics = normalize_meta_list(meta, "topics")
    skills = normalize_meta_list(meta, "skills")
    related = normalize_meta_list(meta, "related")
    sections = split_sections(body)
    written_paths: set[Path] = set()
    actions: list[str] = []

    session_meta = base_node_meta(source_session, "session", title, created, source_session, topics, skills, related)
    session_meta["review"]["next_due"] = (created + timedelta(days=7)).isoformat()
    session_meta["review"]["interval_days"] = 7
    session_path = ROOT / "Daily_Sessions" / f"{created.isoformat()}_{session_slug}.md"
    actions.append(f"{write_node(session_path, session_meta, body)} session: {session_path.relative_to(ROOT)}")
    written_paths.add(session_path)

    vocabulary = find_section(sections, "new vocabulary")
    for term, block in h3_blocks(vocabulary):
        term_slug = slugify(term)
        item_related = parse_list(field(block, "Related words")) or related
        key = node_key(created, session_slug, term_slug)
        node_id = f"vocab_{key}"
        node_meta = base_node_meta(node_id, "vocabulary", term, created, source_session, topics, skills, item_related)
        node_body = "\n".join([
            f"# {term}",
            "",
            f"Meaning:\n{field(block, 'Meaning')}",
            "",
            f"Pronunciation:\n{field(block, 'Pronunciation')}",
            "",
            f"Example:\n{field(block, 'Example')}",
            "",
            f"IELTS usage:\n{field(block, 'IELTS usage')}",
            "",
            f"Related words:\n{', '.join(item_related)}",
        ])
        path = ROOT / "Skill_Tree" / "Vocabulary" / f"{created.isoformat()}_{session_slug}_{term_slug}.md"
        actions.append(f"{write_node(path, node_meta, node_body)} vocabulary: {path.relative_to(ROOT)}")
        written_paths.add(path)

    grammar = find_section(sections, "grammar")
    if grammar:
        blocks = h3_blocks(grammar) or [("Grammar Upgrade", grammar)]
        for index, (grammar_title, block) in enumerate(blocks, start=1):
            original = field(block, "Original")
            better = field(block, "Better")
            explanation = field(block, "Explanation")
            title_text = original[:60] if original else grammar_title
            item_slug = f"grammar_{index}"
            key = node_key(created, session_slug, item_slug)
            node_id = f"grammar_{key}"
            node_meta = base_node_meta(node_id, "grammar_error", title_text, created, source_session, topics, skills, related)
            node_body = "\n".join([
                f"# Grammar Upgrade {index}",
                "",
                f"Original:\n{original}",
                "",
                f"Better:\n{better}",
                "",
                f"Explanation:\n{explanation}",
            ])
            path = ROOT / "Mistake_Log" / f"{created.isoformat()}_{session_slug}_grammar_{index}.md"
            actions.append(f"{write_node(path, node_meta, node_body)} grammar: {path.relative_to(ROOT)}")
            written_paths.add(path)

    pronunciation = find_section(sections, "pronunciation")
    for term, block in h3_blocks(pronunciation):
        term_slug = slugify(term)
        key = node_key(created, session_slug, term_slug)
        node_id = f"pron_{key}"
        node_meta = base_node_meta(node_id, "pronunciation", term, created, source_session, topics, skills, related)
        node_body = "\n".join([
            f"# {term}",
            "",
            f"Pronunciation:\n{field(block, 'Pronunciation')}",
            "",
            f"Common mistake:\n{field(block, 'Common mistake')}",
            "",
            f"Practice sentence:\n{field(block, 'Practice sentence')}",
        ])
        path = ROOT / "Skill_Tree" / "Pronunciation" / f"{created.isoformat()}_{session_slug}_{term_slug}.md"
        actions.append(f"{write_node(path, node_meta, node_body)} pronunciation: {path.relative_to(ROOT)}")
        written_paths.add(path)

    expressions = find_section(sections, "personal expression")
    for expression_title, block in h3_blocks(expressions):
        expression_slug = slugify(expression_title)
        used_for = parse_list(field(block, "Used for"))
        item_related = parse_list(field(block, "Related")) or related
        key = node_key(created, session_slug, expression_slug)
        node_id = f"expr_{key}"
        node_meta = base_node_meta(node_id, "expression", expression_title, created, source_session, unique_list(topics + used_for), skills, item_related)
        node_body = "\n".join([
            f"# {expression_title}",
            "",
            f"Expression:\n{field(block, 'Expression')}",
            "",
            f"Used for:\n{', '.join(used_for)}",
            "",
            f"Related:\n{', '.join(item_related)}",
        ])
        path = ROOT / "Expression_Bank" / f"{created.isoformat()}_{session_slug}_{expression_slug}.md"
        actions.append(f"{write_node(path, node_meta, node_body)} expression: {path.relative_to(ROOT)}")
        written_paths.add(path)

    mini_responses = find_any_section(sections, ["mini speaking", "response bank", "speaking response", "short response"])
    for response_title, block in h3_blocks(mini_responses):
        response_slug = slugify(response_title)
        used_for = parse_list(field(block, "Used for")) or parse_list(field(block, "Reusable for"))
        item_related = parse_list(field(block, "Related")) or related
        response_text = field(block, "Response") or field(block, "Answer") or block.strip()
        structure = field(block, "Structure")
        key = node_key(created, session_slug, response_slug)
        node_id = f"response_{key}"
        node_meta = base_node_meta(node_id, "mini_response", response_title, created, source_session, unique_list(topics + used_for), skills, item_related)
        node_body = "\n".join([
            f"# {response_title}",
            "",
            f"Response:\n{response_text}",
            "",
            f"Used for:\n{', '.join(used_for)}",
            "",
            f"Structure:\n{structure}",
            "",
            f"Related:\n{', '.join(item_related)}",
        ])
        path = ROOT / "Response_Bank" / f"{created.isoformat()}_{session_slug}_{response_slug}.md"
        actions.append(f"{write_node(path, node_meta, node_body)} mini response: {path.relative_to(ROOT)}")
        written_paths.add(path)

    stories = find_section(sections, "personal stories")
    for story_title, block in h3_blocks(stories):
        story_slug = slugify(story_title)
        used_for = parse_list(field(block, "Used for"))
        item_related = parse_list(field(block, "Related")) or related
        key = node_key(created, session_slug, story_slug)
        node_id = f"story_{key}"
        node_meta = base_node_meta(node_id, "personal_story", story_title, created, source_session, unique_list(topics + used_for), skills, item_related)
        node_body = "\n".join([
            f"# {story_title}",
            "",
            f"Story:\n{field(block, 'Story')}",
            "",
            f"Used for:\n{', '.join(used_for)}",
            "",
            f"Related:\n{', '.join(item_related)}",
        ])
        path = ROOT / "Personal_Stories" / f"{created.isoformat()}_{session_slug}_{story_slug}.md"
        actions.append(f"{write_node(path, node_meta, node_body)} story: {path.relative_to(ROOT)}")
        written_paths.add(path)

    removed = cleanup_session_nodes(source_session, written_paths)
    for item in removed:
        actions.append(f"removed legacy node: {item.relative_to(ROOT)}")

    print("\n".join(actions))
    print(f"Processed session: {session_path.relative_to(ROOT)}")
    return session_path


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python scripts/process_session.py inbox/<session-file>.md")
        return 2
    input_path = Path(argv[1])
    if not input_path.is_absolute():
        input_path = ROOT / input_path
    process(input_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
