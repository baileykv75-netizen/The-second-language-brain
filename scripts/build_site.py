from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SKIP_DIRS = {"inbox", "templates", "indexes", ".git", ".github", "scripts", "docs", "prompts"}


def parse_list(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return [item.strip().strip("\"'") for item in value.split(",") if item.strip()]


def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not match:
        return {}, text
    meta: dict[str, object] = {}
    parent = None
    for line in match.group(1).splitlines():
        if not line.strip() or ":" not in line:
            continue
        if line.startswith("  ") and parent:
            key, raw = line.strip().split(":", 1)
            nested = meta.setdefault(parent, {})
            if isinstance(nested, dict):
                raw = raw.strip().strip("\"'")
                nested[key.strip()] = parse_list(raw) if raw.startswith("[") and raw.endswith("]") else raw
            continue
        key, raw = line.split(":", 1)
        key, raw = key.strip(), raw.strip()
        parent = key if not raw else None
        if raw.startswith("[") and raw.endswith("]"):
            meta[key] = parse_list(raw)
        elif raw:
            meta[key] = raw.strip("\"'")
        else:
            meta[key] = {}
    return meta, text[match.end():]


def readable_body(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"^#+\s*", "", text, flags=re.M)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def excerpt(text: str, limit: int = 210) -> str:
    plain = re.sub(r"\s+", " ", readable_body(text)).strip()
    return plain if len(plain) <= limit else plain[: limit - 3].rstrip() + "..."


def section_text(body: str, heading: str, limit: int = 420) -> str:
    match = re.search(rf"^##\s+{re.escape(heading)}\s*$\n?(.*?)(?=^##\s+|\Z)", body, re.M | re.S | re.I)
    if not match:
        return ""
    value = re.sub(r"\s+", " ", match.group(1)).strip()
    return value[:limit]


def node_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def iter_nodes() -> list[dict]:
    nodes: list[dict] = []
    for path in ROOT.rglob("*.md"):
        if set(path.relative_to(ROOT).parts) & SKIP_DIRS:
            continue
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        if not meta.get("id") or not meta.get("type"):
            continue
        review = meta.get("review") if isinstance(meta.get("review"), dict) else {}
        nodes.append({
            "id": meta["id"],
            "type": meta["type"],
            "title": meta.get("title", path.stem),
            "created": meta.get("created", ""),
            "source_session": meta.get("source_session", ""),
            "source_case": meta.get("source_case", ""),
            "topics": meta.get("topics", []) if isinstance(meta.get("topics"), list) else [],
            "skills": meta.get("skills", []) if isinstance(meta.get("skills"), list) else [],
            "related": meta.get("related", []) if isinstance(meta.get("related"), list) else [],
            "review": review,
            "source_url": meta.get("source_url", ""),
            "source_title": meta.get("source_title", ""),
            "source_excerpt": meta.get("source_excerpt", ""),
            "path": node_path(path),
            "excerpt": excerpt(body),
            "body": readable_body(body),
            "question": section_text(body, "IELTS Speaking Question", 300),
            "final_position": section_text(body, "Challenge And Reasoning", 360),
        })
    return sorted(nodes, key=lambda item: (str(item["created"]), str(item["title"])), reverse=True)


def parse_due(node: dict) -> date | None:
    try:
        return datetime.strptime(str(node.get("review", {}).get("next_due", "")), "%Y-%m-%d").date()
    except ValueError:
        return None


def review_prompt(node: dict) -> str:
    focus = str(node.get("review", {}).get("next_focus") or "Build a clear answer before using advanced language.")
    question = node.get("question") or "Explain your view on this topic."
    return "\n".join([
        "开始今日复习",
        f"Case ID: {node['id']}",
        f"Case: {node['title']}",
        f"Question: {question}",
        "Please act as my objective IELTS Speaking coach. Ask me to answer for 60 seconds before showing any old answer or language notes.",
        f"Focus for this attempt: {focus}",
        "After feedback, wait for me to say 完成复习 before writing a REVIEW_UPDATE.",
    ])


def choose_speak_tasks(nodes: list[dict], today: date) -> list[dict]:
    cases = [node for node in nodes if node["type"] == "speaking_case"]
    due = sorted((node for node in cases if (parse_due(node) or today) <= today), key=lambda item: parse_due(item) or today)
    recent = sorted(cases, key=lambda item: str(item.get("created", "")), reverse=True)
    tasks: list[dict] = []

    def add(node: dict) -> None:
        if node["id"] not in {item["id"] for item in tasks} and len(tasks) < 3:
            item = dict(node)
            item["due_date"] = (parse_due(node) or today).isoformat()
            item["prompt"] = review_prompt(node)
            tasks.append(item)

    if due:
        add(due[0])
    if recent:
        add(recent[0])
    current_topics = {topic for task in tasks for topic in task.get("topics", [])}
    for node in due[1:] + recent[1:]:
        if not set(node.get("topics", [])) & current_topics:
            add(node)
            break
    for node in due[1:] + recent[1:]:
        add(node)
    return tasks


def group_counts(nodes: list[dict], key: str) -> list[dict]:
    counter: Counter[str] = Counter()
    for node in nodes:
        counter.update(str(item) for item in node.get(key, []))
    return [{"name": name, "count": count} for name, count in counter.most_common()]


def build_payload(nodes: list[dict]) -> dict:
    today = date.today()
    due = [node for node in nodes if node["type"] == "speaking_case" and (parse_due(node) or today) <= today]
    upcoming = [node for node in nodes if node["type"] == "speaking_case" and (parse_due(node) or today) > today]
    for node in due + upcoming:
        node["due_date"] = (parse_due(node) or today).isoformat()
        node["prompt"] = review_prompt(node)
    stats = {
        "total": len(nodes),
        "speakingCases": sum(node["type"] == "speaking_case" for node in nodes),
        "sessions": sum(node["type"] == "session" for node in nodes),
        "vocabulary": sum(node["type"] == "vocabulary" for node in nodes),
        "grammarMistakes": sum(node["type"] == "grammar_error" for node in nodes),
        "expressions": sum(node["type"] == "expression" for node in nodes),
        "responses": sum(node["type"] == "mini_response" for node in nodes),
        "stories": sum(node["type"] == "personal_story" for node in nodes),
    }
    return {
        "generated_on": today.isoformat(), "stats": stats, "nodes": nodes,
        "due": sorted(due, key=lambda item: item["due_date"]),
        "upcoming": sorted(upcoming, key=lambda item: item["due_date"]),
        "speak_tasks": choose_speak_tasks(nodes, today),
        "topics": group_counts(nodes, "topics"), "skills": group_counts(nodes, "skills"),
    }


INDEX_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#173f36"><title>The Second Language Brain</title><link rel="manifest" href="manifest.json"><link rel="stylesheet" href="styles.css"></head>
<body><header><div><p class="eyebrow">SPEAKING-FIRST IELTS SYSTEM</p><h1>The Second Language Brain</h1><p>Read for ideas. Think critically. Speak from your own position.</p></div><a href="https://github.com/baileykv75-netizen/The-second-language-brain">Repository</a></header>
<main><section class="today"><div><span>Today: Speak</span><h2 id="today-title">Loading your practice...</h2><p id="today-copy"></p></div><div class="stats" id="stats"></div></section>
<section><div class="section-heading"><div><p class="eyebrow">DO BEFORE YOU LOOK</p><h2>Today's speaking tasks</h2></div><span id="task-count"></span></div><div id="speak-tasks" class="task-list"></div></section>
<section class="browse"><label for="search">Browse your brain</label><input id="search" type="search" placeholder="Search words, themes, or speaking skills"><div id="filters" class="filters"></div><nav><button data-filter="all">All</button><button class="active" data-filter="speaking_case">Cases</button><button data-filter="session">Sessions</button><button data-filter="vocabulary">Words</button><button data-filter="grammar_error">Mistakes</button><button data-filter="expression">Phrases</button><button data-filter="mini_response">Responses</button></nav></section>
<section><div class="section-heading"><h2 id="results-title">Speaking cases</h2><span id="result-count"></span></div><div id="cards" class="cards"></div></section></main>
<aside id="detail" aria-hidden="true"><div data-close></div><article><button class="close" data-close aria-label="Close">x</button><p id="detail-type" class="eyebrow"></p><h2 id="detail-title"></h2><p id="detail-meta"></p><div id="detail-tags" class="tags"></div><a id="detail-source" target="_blank" rel="noreferrer"></a><button id="detail-copy" class="copy hidden">Copy review task</button><pre id="detail-body"></pre></article></aside><script src="app.js"></script></body></html>"""


STYLES = """:root{--ink:#173f36;--green:#23765f;--paper:#f6f4ed;--panel:#fff;--line:#d9ddd4;--muted:#637069;--warm:#c46234}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 Inter,system-ui,sans-serif}header{display:flex;justify-content:space-between;gap:24px;padding:32px max(20px,calc((100vw - 1040px)/2));background:var(--ink);color:#fff}header h1{margin:4px 0;font-size:38px;letter-spacing:0}header p{margin:0;color:#d7e8df}header a{align-self:flex-start;border:1px solid #8eada1;border-radius:6px;padding:7px 10px;color:#fff;text-decoration:none}.eyebrow{margin:0;color:var(--green);font-size:12px;font-weight:800;letter-spacing:.08em}.today{display:grid;grid-template-columns:1fr auto;gap:24px;margin:24px 0;padding:22px;border-left:4px solid var(--warm);background:var(--panel)}.today span{color:var(--warm);font-weight:800}.today h2{margin:4px 0}.today p{margin:0;color:var(--muted)}main{width:min(1040px,100%);margin:auto;padding:0 20px 64px}.stats{display:grid;grid-template-columns:repeat(2,88px);gap:8px}.stat{padding:10px;border:1px solid var(--line);background:#fafbf8;text-align:center}.stat strong{display:block;font-size:22px}.stat small{color:var(--muted)}section{margin:28px 0}.section-heading{display:flex;justify-content:space-between;align-items:end;margin-bottom:12px}.section-heading h2{margin:0}.section-heading span{color:var(--muted)}.task-list{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.task{min-height:230px;padding:16px;border:1px solid var(--line);background:var(--panel)}.task .due{color:var(--warm);font-size:13px;font-weight:700}.task h3{margin:8px 0;font-size:18px}.task p{color:var(--muted);font-size:14px}.task button,.copy{width:100%;border:0;border-radius:5px;padding:10px;background:var(--ink);color:#fff;font-weight:700;cursor:pointer}.browse{padding:18px;background:#e9f1ec;border:1px solid #cbdad2}.browse label{font-weight:800}.browse input{width:100%;margin:8px 0 12px;padding:11px;border:1px solid var(--line);border-radius:4px;background:#fff;font:inherit}.filters,nav,.tags{display:flex;flex-wrap:wrap;gap:7px}nav{margin-top:12px}nav button,.filters button,.tag{border:1px solid #b9cbc2;border-radius:4px;padding:6px 9px;background:#fff;color:var(--ink);cursor:pointer}nav button.active{background:var(--ink);color:#fff}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.card{min-height:185px;padding:15px;border:1px solid var(--line);background:var(--panel);text-align:left;cursor:pointer}.card:hover{border-color:var(--green)}.card h3{margin:6px 0;font-size:19px}.card p{color:var(--muted);font-size:14px}.tag{font-size:12px;background:#f3f7f4}.empty{padding:24px;border:1px dashed var(--line);text-align:center;color:var(--muted)}#detail{position:fixed;inset:0;display:none;z-index:10}#detail.open{display:block}#detail>div{position:absolute;inset:0;background:#102b2499}#detail article{position:absolute;right:max(16px,calc((100vw - 900px)/2));top:18px;bottom:18px;width:min(860px,calc(100vw - 32px));overflow:auto;padding:24px;background:#fff}.close{float:right;border:0;background:none;font-size:24px;cursor:pointer}#detail-meta{color:var(--muted);font-size:13px}#detail-source{display:block;margin:12px 0;color:var(--green)}#detail-body{white-space:pre-wrap;overflow-wrap:anywhere;margin-top:16px;padding:16px;background:#f7f8f5;border:1px solid var(--line);font:15px/1.65 Inter,system-ui,sans-serif}.hidden{display:none}@media(max-width:760px){header{padding:22px 16px}header h1{font-size:30px}.today{grid-template-columns:1fr}.task-list,.cards{grid-template-columns:1fr}.stats{grid-template-columns:repeat(4,1fr)}.stats small{font-size:11px}main{padding-inline:12px}#detail article{inset:10px;width:auto}}
"""


APP_JS = """const state={data:null,filter:'speaking_case',query:'',topic:''};const $=s=>document.querySelector(s);const labels={speaking_case:'Speaking case',session:'Session',vocabulary:'Word',grammar_error:'Mistake',pronunciation:'Pronunciation',expression:'Phrase',mini_response:'Response',personal_story:'Story'};const esc=v=>String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
function matches(n){const q=state.query.toLowerCase();const text=[n.title,n.type,n.excerpt,...n.topics,...n.skills,...n.related].join(' ').toLowerCase();return(state.filter==='all'||n.type===state.filter)&&(!q||text.includes(q))&&(!state.topic||n.topics.includes(state.topic))}function cards(){const items=state.data.nodes.filter(matches);$('#result-count').textContent=`${items.length} items`;$('#results-title').textContent=state.topic?`Topic: ${state.topic}`:(state.filter==='speaking_case'?'Speaking cases':'Knowledge nodes');$('#cards').innerHTML=items.length?items.map(n=>`<button class="card" data-node="${esc(n.id)}"><p class="eyebrow">${esc(labels[n.type]||n.type)}</p><h3>${esc(n.title)}</h3><p>${esc(n.excerpt)}</p><div class="tags">${n.topics.slice(0,2).map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div></button>`).join(''):'<div class="empty">No matching material yet.</div>'}function tasks(){const items=state.data.speak_tasks;$('#task-count').textContent=`${items.length} tasks`;$('#today-title').textContent=items.length?`${items.length} speaking tasks are ready`:'No speaking case yet';$('#today-copy').textContent=items.length?'Speak first. Open the task only after you have tried your own answer.':'Save your first confirmed case in ChatGPT to begin.';$('#speak-tasks').innerHTML=items.length?items.map(n=>`<article class="task"><span class="due">Due ${esc(n.due_date)}</span><h3>${esc(n.title)}</h3><p>${esc(n.question||'Explain your view on this topic.')}</p><button data-copy="${esc(n.id)}">Copy task for ChatGPT</button></article>`).join(''):'<div class="empty">Your next saved case will appear here.</div>'}function stats(){const s=state.data.stats;$('#stats').innerHTML=[['Cases',s.speakingCases],['Words',s.vocabulary],['Mistakes',s.grammarMistakes],['Responses',s.responses]].map(([a,b])=>`<div class="stat"><strong>${b}</strong><small>${a}</small></div>`).join('')}function filters(){$('#filters').innerHTML=state.data.topics.slice(0,10).map(t=>`<button data-topic="${esc(t.name)}">${esc(t.name)} ${t.count}</button>`).join('')}function copy(text){navigator.clipboard?.writeText(text).then(()=>alert('Copied. Paste it into your ChatGPT Project.')).catch(()=>window.prompt('Copy this review task:',text))}function open(id){const n=state.data.nodes.find(x=>x.id===id);if(!n)return;$('#detail-type').textContent=labels[n.type]||n.type;$('#detail-title').textContent=n.title;$('#detail-meta').textContent=`${n.created} · ${n.path}`;$('#detail-tags').innerHTML=[...n.topics,...n.skills].map(t=>`<span class="tag">${esc(t)}</span>`).join('');const source=$('#detail-source');source.href=n.source_url||'#';source.textContent=n.source_url?`Source: ${n.source_title||n.source_url}`:'';source.classList.toggle('hidden',!n.source_url);const button=$('#detail-copy');button.classList.toggle('hidden',n.type!=='speaking_case');button.onclick=()=>copy(n.prompt);$('#detail-body').textContent=n.body;$('#detail').classList.add('open');$('#detail').setAttribute('aria-hidden','false')}function bind(){$('#search').addEventListener('input',e=>{state.query=e.target.value;cards()});document.addEventListener('click',e=>{const filter=e.target.closest('[data-filter]');if(filter){state.filter=filter.dataset.filter;state.topic='';document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b===filter));cards()}const topic=e.target.closest('[data-topic]');if(topic){state.topic=topic.dataset.topic;state.filter='all';document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.filter==='all'));cards()}const node=e.target.closest('[data-node]');if(node)open(node.dataset.node);const copyButton=e.target.closest('[data-copy]');if(copyButton){const n=state.data.speak_tasks.find(x=>x.id===copyButton.dataset.copy);if(n)copy(n.prompt)}if(e.target.closest('[data-close]')){$('#detail').classList.remove('open');$('#detail').setAttribute('aria-hidden','true')}})}async function main(){state.data=await fetch('data.json',{cache:'no-store'}).then(r=>r.json());stats();tasks();filters();cards();bind()}main().catch(()=>{$('#cards').innerHTML='<div class="empty">The learning app could not load its data.</div>'});"""


def write_assets() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    (DOCS / "manifest.json").write_text(json.dumps({"name": "The Second Language Brain", "short_name": "Language Brain", "start_url": "./", "display": "standalone", "background_color": "#f6f4ed", "theme_color": "#173f36"}, indent=2) + "\n", encoding="utf-8")
    (DOCS / "index.html").write_text(INDEX_HTML.rstrip() + "\n", encoding="utf-8")
    (DOCS / "styles.css").write_text(STYLES.rstrip() + "\n", encoding="utf-8")
    (DOCS / "app.js").write_text(APP_JS.rstrip() + "\n", encoding="utf-8")


def build(root: Path = ROOT) -> None:
    if root != ROOT:
        raise ValueError("The static site builder expects the repository root.")
    write_assets()
    payload = build_payload(iter_nodes())
    (DOCS / "data.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote website data: docs/data.json ({len(payload['nodes'])} nodes)")


def main(argv: list[str]) -> int:
    build(ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
