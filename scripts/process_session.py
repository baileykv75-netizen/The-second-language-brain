from __future__ import annotations

import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW_INTERVALS = [1, 3, 7, 14, 30]


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


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not match:
        return {}, text
    meta: dict[str, object] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        raw = raw.strip()
        if raw.startswith("[") and raw.endswith("]"):
            meta[key] = parse_list(raw)
        else:
            meta[key] = raw.strip("\"'")
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
        rf"^{re.escape(label)}:\s*\n(.*?)(?=^[A-Z][A-Za-z ]+:\s*$|\Z)",
        re.M | re.S,
    )
    match = pattern.search(block)
    return match.group(1).strip() if match else ""


def find_section(sections: dict[str, str], keyword: str) -> str:
    for title, body in sections.items():
        if keyword in title:
            return body
    return ""


def write_node(path: Path, meta: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter(meta) + body.strip() + "\n", encoding="utf-8")


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


def base_node_meta(node_id: str, node_type: str, title: str, created: date, source_session: str, topics: list[str], skills: list[str], related: list[str]) -> dict:
    return {
        "id": node_id,
        "type": node_type,
        "title": title,
        "created": created.isoformat(),
        "source_session": source_session,
        "topics": topics,
        "skills": skills,
        "related": related,
        "review": {
            "status": "new",
            "next_due": (created + timedelta(days=REVIEW_INTERVALS[0])).isoformat(),
            "interval_days": REVIEW_INTERVALS[0],
        },
    }


def process(input_path: Path) -> None:
    raw_text = input_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw_text)
    created = session_date(input_path, meta)
    title = str(meta.get("title") or input_path.stem)
    session_slug = slugify(title)
    source_session = f"session_{created.strftime('%Y%m%d')}_{session_slug}"
    topics = normalize_meta_list(meta, "topics")
    skills = normalize_meta_list(meta, "skills")
    related = normalize_meta_list(meta, "related")
    sections = split_sections(body)

    session_meta = base_node_meta(source_session, "session", title, created, source_session, topics, skills, related)
    session_meta["review"]["next_due"] = (created + timedelta(days=7)).isoformat()
    session_meta["review"]["interval_days"] = 7
    session_path = ROOT / "Daily_Sessions" / f"{created.isoformat()}_{session_slug}.md"
    write_node(session_path, session_meta, body)

    vocabulary = find_section(sections, "new vocabulary")
    for term, block in h3_blocks(vocabulary):
        term_slug = slugify(term)
        item_related = parse_list(field(block, "Related words")) or related
        node_id = f"vocab_{term_slug}_{created.strftime('%Y%m%d')}"
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
        write_node(ROOT / "Skill_Tree" / "Vocabulary" / f"{term_slug}.md", node_meta, node_body)

    grammar = find_section(sections, "grammar")
    if grammar:
        blocks = h3_blocks(grammar) or [("Grammar Upgrade", grammar)]
        for index, (grammar_title, block) in enumerate(blocks, start=1):
            original = field(block, "Original")
            better = field(block, "Better")
            explanation = field(block, "Explanation")
            title_text = original[:60] if original else grammar_title
            node_id = f"grammar_{created.strftime('%Y%m%d')}_{index}"
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
            write_node(ROOT / "Mistake_Log" / f"{created.isoformat()}_grammar_{index}.md", node_meta, node_body)

    pronunciation = find_section(sections, "pronunciation")
    for term, block in h3_blocks(pronunciation):
        term_slug = slugify(term)
        node_id = f"pron_{term_slug}_{created.strftime('%Y%m%d')}"
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
        write_node(ROOT / "Skill_Tree" / "Pronunciation" / f"{term_slug}.md", node_meta, node_body)

    expressions = find_section(sections, "personal expression")
    for expression_title, block in h3_blocks(expressions):
        expression_slug = slugify(expression_title)
        used_for = parse_list(field(block, "Used for"))
        item_related = parse_list(field(block, "Related")) or related
        node_id = f"expr_{expression_slug}_{created.strftime('%Y%m%d')}"
        node_meta = base_node_meta(node_id, "expression", expression_title, created, source_session, topics + used_for, skills, item_related)
        node_body = "\n".join([
            f"# {expression_title}",
            "",
            f"Expression:\n{field(block, 'Expression')}",
            "",
            f"Used for:\n{', '.join(used_for)}",
            "",
            f"Related:\n{', '.join(item_related)}",
        ])
        write_node(ROOT / "Expression_Bank" / f"{expression_slug}.md", node_meta, node_body)

    stories = find_section(sections, "personal stories")
    for story_title, block in h3_blocks(stories):
        story_slug = slugify(story_title)
        used_for = parse_list(field(block, "Used for"))
        item_related = parse_list(field(block, "Related")) or related
        node_id = f"story_{story_slug}_{created.strftime('%Y%m%d')}"
        node_meta = base_node_meta(node_id, "personal_story", story_title, created, source_session, topics + used_for, skills, item_related)
        node_body = "\n".join([
            f"# {story_title}",
            "",
            f"Story:\n{field(block, 'Story')}",
            "",
            f"Used for:\n{', '.join(used_for)}",
            "",
            f"Related:\n{', '.join(item_related)}",
        ])
        write_node(ROOT / "Personal_Stories" / f"{story_slug}.md", node_meta, node_body)

    import build_indexes
    import build_review

    build_indexes.build(ROOT)
    build_review.build(ROOT, created)
    print(f"Processed session: {session_path.relative_to(ROOT)}")


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

