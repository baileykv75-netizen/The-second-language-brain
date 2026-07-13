from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path


SECTION_MAP = {
    "summary": "Conversation Summary",
    "new vocabulary": "New Vocabulary",
    "grammar corrections": "Grammar Upgrade",
    "speaking patterns": "Mini Speaking Responses",
    "personal philosophy": "Personal Expression Bank",
    "personal story": "Personal Stories",
    "ielts topics": "Topic Links",
    "review tasks": "Review Tasks",
}


def parse_list(value: str) -> list[str]:
    value = value.strip().strip("[]")
    return [item.strip().strip("-* ").strip("\"'") for item in re.split(r"[,;\n]", value) if item.strip().strip("-* ")]


def session_date(input_path: Path) -> date:
    match = re.search(r"(\d{4}-\d{2}-\d{2})", input_path.name)
    if match:
        return datetime.strptime(match.group(1), "%Y-%m-%d").date()
    return date.today()


def title_from_path(input_path: Path) -> str:
    stem = re.sub(r"^\d{4}-\d{2}-\d{2}_?", "", input_path.stem)
    return stem.replace("_", " ").strip().title() or "Untitled Session"


def split_loose_sections(text: str) -> tuple[dict[str, str], str]:
    lines = text.replace("\r\n", "\n").splitlines()
    sections: dict[str, list[str]] = {}
    current = ""
    session_id = ""
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current:
                sections.setdefault(current, []).append("")
            continue
        session_match = re.match(r"^Session ID:\s*(.+)$", stripped, re.I)
        if session_match:
            session_id = session_match.group(1).strip()
            continue
        key = stripped.rstrip(":").lower()
        if key == "session_update":
            continue
        if key in SECTION_MAP:
            current = key
            sections.setdefault(current, [])
            continue
        if current:
            sections.setdefault(current, []).append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items()}, session_id


def ensure_block_heading(section_name: str, body: str, fallback_title: str) -> str:
    if not body or re.search(r"^###\s+", body, re.M):
        return body
    if section_name == "personal philosophy":
        return f"### {fallback_title} Philosophy\n\nExpression:\n{body}\n\nUsed for:\nOpinion questions, Personal Philosophy"
    if section_name == "speaking patterns":
        return f"### {fallback_title} Response\n\nResponse:\n{body}\n\nUsed for:\nOpinion questions\n\nStructure:\nmain idea -> support -> example"
    if section_name == "personal story":
        return f"### {fallback_title} Story\n\nStory:\n{body}\n\nUsed for:\nExperiences, Personal stories"
    return body


def normalize_text(text: str, input_path: Path) -> str:
    if text.lstrip().startswith("---"):
        return text
    if "SESSION_UPDATE" not in text[:200].upper():
        return text

    sections, session_id = split_loose_sections(text)
    title = session_id or title_from_path(input_path)
    created = session_date(input_path)
    topics = parse_list(sections.get("ielts topics", ""))

    output = [
        "---",
        f"title: {title}",
        f"date: {created.isoformat()}",
        f"topics: [{', '.join(topics)}]",
        "skills: []",
        "related: []",
        "---",
        "",
        "# Session Topic",
        "",
        title,
        "",
    ]

    for loose_name, target_name in SECTION_MAP.items():
        if loose_name == "ielts topics":
            continue
        body = ensure_block_heading(loose_name, sections.get(loose_name, ""), title)
        if not body:
            continue
        output.extend([f"## {target_name}", "", body, ""])

    if topics:
        output.extend(["## Topic Links", "", *[f"- {topic}" for topic in topics], ""])

    return "\n".join(output).rstrip() + "\n"
