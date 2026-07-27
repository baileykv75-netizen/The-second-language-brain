from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import process_session


ROOT = Path(__file__).resolve().parents[1]
SEEDS = {
    "session_20260712_ai_game_ideas": {
        "case_id": "case_20260712_ai_game_ideas",
        "question": "What kind of game would you like to develop, and why would it be meaningful?",
        "initial": "I want to design a game where creatures survive in an ecosystem.",
        "counter": "A complex system can be difficult for players to understand. Why would this be more engaging than a simple competitive game?",
        "position": "I value an ecosystem-based game because changing conditions, rather than a fixed winner, can make players think about adaptation, balance, and long-term consequences.",
        "source_note": "This is a migrated legacy speaking session. No article source was stored for it.",
        "topics": ["Technology", "Games", "Environment", "Opinion Questions"],
    },
    "session_20260712_ai_consciousness_and_evolution": {
        "case_id": "case_20260712_ai_consciousness_and_evolution",
        "question": "If artificial intelligence developed consciousness, should it have rights?",
        "initial": "I currently see AI as a tool created by humans.",
        "counter": "How could society distinguish genuine consciousness from convincing behaviour, and what practical rights would follow?",
        "position": "If AI developed genuine consciousness, its moral status should depend on consciousness and intrinsic value rather than biological identity alone, while society would still need careful evidence and safeguards.",
        "source_note": "This is a migrated legacy speaking session. No article source was stored for it.",
        "topics": ["Technology", "Artificial Intelligence", "Future Society", "Ethics", "Opinion Questions"],
    },
    "session_20260716_herbicide_free_campus_article_practice": {
        "case_id": "case_20260716_herbicide_free_campus_article_practice",
        "question": "Should universities use potentially harmful chemicals when they are useful for research?",
        "initial": "I think it depends on the purpose and the level of risk.",
        "counter": "Could a strict safety rule make a harmful chemical acceptable, or should universities always choose the least harmful alternative?",
        "position": "Essential research may justify controlled chemical use, but universities should stop using chemicals that harm people or contaminate waterways and should actively seek safer alternatives.",
        "source_note": "This is a migrated article-practice session. The original article link was not stored, so this case records only the user's summary and speaking position.",
        "topics": ["Environment", "Education", "Health", "Climate Change", "Opinion Questions"],
    },
}


def answer_section(body: str) -> str:
    sections = process_session.split_sections(body)
    return process_session.find_any_section(sections, ["band 7.5", "model answer"]).strip()


def case_body(seed: dict, model_answer: str) -> str:
    short = next((paragraph.strip() for paragraph in model_answer.split("\n\n") if paragraph.strip()), model_answer).strip()
    return "\n".join([
        "# Speaking Case", "",
        "## Source Material", "", "### Source Fact", "", seed["source_note"], "",
        "### My Summary", "", "Recovered from a previous IELTS speaking session.", "",
        "## IELTS Speaking Question", "", seed["question"], "",
        "## My Initial Position", "", seed["initial"], "",
        "## Challenge And Reasoning", "", "### Counterargument", "", seed["counter"], "",
        "### Final Position", "", seed["position"], "",
        "## Speaking Answers", "", "### 30 Seconds", "", short, "",
        "### 60 Seconds", "", model_answer or "See the linked legacy session.", "",
        "### 2 Minutes", "", model_answer or "See the linked legacy session.", "",
        "## Linked Legacy Session", "", "The original session remains in Daily_Sessions and all existing knowledge nodes are preserved.",
    ])


def migrate() -> None:
    created = 0
    linked = 0
    for session_path in sorted((ROOT / "Daily_Sessions").glob("*.md")):
        meta, body = process_session.parse_frontmatter(session_path.read_text(encoding="utf-8"))
        session_id = str(meta.get("id") or "")
        seed = SEEDS.get(session_id)
        if not seed:
            continue
        created_date = process_session.session_date(session_path, meta)
        case_path = ROOT / "Speaking_Cases" / f"{created_date.isoformat()}_{process_session.slugify(str(meta.get('title') or session_path.stem))}.md"
        case_meta = process_session.base_node_meta(
            seed["case_id"], "speaking_case", str(meta.get("title") or session_path.stem), created_date,
            session_id, seed["topics"], meta.get("skills", []), meta.get("related", []), seed["case_id"],
        )
        case_meta.update({"source_url": "", "source_title": "", "source_excerpt": ""})
        case_meta["review"] = {
            "status": "active", "stage": 0,
            "next_due": (created_date + timedelta(days=1)).isoformat(), "interval_days": 1,
            "completed_dates": [], "last_feedback": "", "next_focus": "",
        }
        process_session.write_node(case_path, case_meta, case_body(seed, answer_section(body)))
        created += 1

        for node_path in ROOT.rglob("*.md"):
            if "inbox" in node_path.parts or node_path == case_path:
                continue
            node_meta, node_body = process_session.parse_frontmatter(node_path.read_text(encoding="utf-8"))
            if node_meta.get("source_session") == session_id:
                node_meta["source_case"] = seed["case_id"]
                process_session.write_node(node_path, node_meta, node_body)
                linked += 1
    print(f"Migrated {created} speaking cases and linked {linked} legacy nodes.")


if __name__ == "__main__":
    migrate()
