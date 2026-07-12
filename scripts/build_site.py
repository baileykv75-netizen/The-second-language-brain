from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SKIP_DIRS = {"inbox", "templates", "indexes", ".git", "scripts", "docs"}


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
    return meta, text[match.end():]


def strip_markdown(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"^#+\s*", "", text, flags=re.M)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_`>#-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def readable_body(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"^#+\s*", "", text, flags=re.M)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_`>#]+", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def excerpt(text: str, limit: int = 180) -> str:
    value = strip_markdown(text)
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def iter_nodes() -> list[dict]:
    nodes = []
    for path in ROOT.rglob("*.md"):
        parts = set(path.relative_to(ROOT).parts)
        if parts & SKIP_DIRS:
            continue
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        if not meta.get("id") or not meta.get("type"):
            continue
        review = meta.get("review", {})
        if not isinstance(review, dict):
            review = {}
        nodes.append(
            {
                "id": meta.get("id"),
                "type": meta.get("type"),
                "title": meta.get("title", path.stem),
                "created": meta.get("created", ""),
                "source_session": meta.get("source_session", ""),
                "topics": meta.get("topics", []) if isinstance(meta.get("topics"), list) else [],
                "skills": meta.get("skills", []) if isinstance(meta.get("skills"), list) else [],
                "related": meta.get("related", []) if isinstance(meta.get("related"), list) else [],
                "review": review,
                "path": rel(path),
                "excerpt": excerpt(body),
                "body": readable_body(body),
            }
        )
    return sorted(nodes, key=lambda item: str(item.get("created", "")), reverse=True)


def group_counts(nodes: list[dict], key: str) -> list[dict]:
    counter: Counter[str] = Counter()
    for node in nodes:
        for item in node.get(key, []):
            counter[str(item)] += 1
    return [{"name": name, "count": count} for name, count in counter.most_common()]


def due_items(nodes: list[dict], today: date) -> tuple[list[dict], list[dict]]:
    due = []
    upcoming = []
    for node in nodes:
        next_due = node.get("review", {}).get("next_due")
        if not next_due:
            continue
        try:
            due_date = datetime.strptime(str(next_due), "%Y-%m-%d").date()
        except ValueError:
            continue
        item = dict(node)
        item["due_date"] = due_date.isoformat()
        if due_date <= today:
            due.append(item)
        else:
            upcoming.append(item)
    due.sort(key=lambda item: item["due_date"])
    upcoming.sort(key=lambda item: item["due_date"])
    return due, upcoming


def write_static_assets() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    (DOCS / "manifest.json").write_text(
        json.dumps(
            {
                "name": "The Second Language Brain",
                "short_name": "Language Brain",
                "start_url": "./",
                "display": "standalone",
                "background_color": "#f6f1e8",
                "theme_color": "#13231b",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    (DOCS / "index.html").write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#13231b">
  <title>The Second Language Brain</title>
  <link rel="manifest" href="manifest.json">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="app-header">
    <div>
      <p class="eyebrow">IELTS Speaking Second Brain</p>
      <h1>The Second Language Brain</h1>
      <p class="lede">An AI-assisted English growth system: ChatGPT creates knowledge, GitHub stores memory, Codex maintains structure, and this site visualizes review.</p>
    </div>
    <a class="github-link" href="https://github.com/baileykv75-netizen/The-second-language-brain">GitHub</a>
  </header>

  <main>
    <section class="hero-grid">
      <article class="focus-card">
        <span class="label">Today</span>
        <h2 id="today-title">Review queue</h2>
        <p id="today-copy">Loading your review list...</p>
        <div class="action-row">
          <button class="primary-action" data-filter="due">Start review</button>
          <button class="ghost-action" data-filter="all">Browse all</button>
        </div>
      </article>
      <div class="stats-grid" id="stats"></div>
    </section>

    <section class="search-panel">
      <label for="search">Search your brain</label>
      <input id="search" type="search" placeholder="Try: adapt, environment, explain reasons">
      <div class="chips" id="quick-filters"></div>
    </section>

    <nav class="tab-bar" aria-label="Content sections">
      <button class="tab active" data-filter="all">All</button>
      <button class="tab" data-filter="session">Sessions</button>
      <button class="tab" data-filter="vocabulary">Words</button>
      <button class="tab" data-filter="grammar_error">Mistakes</button>
      <button class="tab" data-filter="expression">Expressions</button>
      <button class="tab" data-filter="mini_response">Responses</button>
      <button class="tab" data-filter="personal_story">Stories</button>
    </nav>

    <section class="section-grid">
      <article class="panel">
        <div class="panel-heading">
          <h2>Due and upcoming</h2>
          <span id="review-count">0 items</span>
        </div>
        <div id="review-list" class="compact-list"></div>
      </article>

      <article class="panel">
        <div class="panel-heading">
          <h2>Topics</h2>
          <span>Reusable links</span>
        </div>
        <div id="topic-cloud" class="tag-cloud"></div>
      </article>
    </section>

    <section class="panel">
      <div class="panel-heading">
        <h2 id="results-title">Knowledge nodes</h2>
        <span id="result-count">0 items</span>
      </div>
      <div id="cards" class="card-grid"></div>
    </section>
  </main>

  <nav class="bottom-nav" aria-label="Quick navigation">
    <button data-filter="due">Review</button>
    <button data-filter="session">Sessions</button>
    <button data-filter="vocabulary">Words</button>
    <button data-filter="mini_response">Responses</button>
    <button data-filter="all">All</button>
  </nav>

  <aside class="detail-panel" id="detail-panel" aria-hidden="true">
    <div class="detail-backdrop" data-close-detail></div>
    <article class="detail-card" role="dialog" aria-modal="true" aria-labelledby="detail-title">
      <button class="detail-close" data-close-detail>Close</button>
      <span class="node-type" id="detail-type"></span>
      <h2 id="detail-title"></h2>
      <p id="detail-meta"></p>
      <div id="detail-tags" class="meta-row"></div>
      <pre id="detail-body"></pre>
    </article>
  </aside>

  <script src="app.js"></script>
</body>
</html>
""",
        encoding="utf-8",
    )

    (DOCS / "styles.css").write_text(
        """:root {
  color-scheme: light;
  --ink: #14231c;
  --muted: #627067;
  --line: #ded7ca;
  --paper: #fbf8f0;
  --panel: #ffffff;
  --accent: #1f6f5b;
  --accent-2: #9b4d2d;
  --accent-3: #315f9b;
  --soft: #edf4f1;
  --shadow: 0 18px 45px rgba(29, 41, 35, 0.12);
}

* { box-sizing: border-box; }

body {
  margin: 0;
  min-height: 100vh;
  background: var(--paper);
  color: var(--ink);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.5;
}

a { color: inherit; text-decoration: none; }
button, input { font: inherit; }

.app-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 28px clamp(18px, 4vw, 48px) 20px;
  background: #13231b;
  color: #fffaf0;
}

.eyebrow {
  margin: 0 0 8px;
  color: #b8d9c9;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h1, h2, p { margin-top: 0; }
h1 { margin-bottom: 10px; font-size: clamp(32px, 6vw, 58px); line-height: 1.02; letter-spacing: 0; }
h2 { margin-bottom: 8px; font-size: 20px; letter-spacing: 0; }
.lede { max-width: 680px; margin-bottom: 0; color: #d8e5dc; }

.github-link {
  align-self: flex-start;
  border: 1px solid rgba(255, 255, 255, 0.28);
  border-radius: 999px;
  padding: 8px 14px;
  color: #fffaf0;
  white-space: nowrap;
}

main {
  width: min(1180px, 100%);
  margin: 0 auto;
  padding: 22px clamp(14px, 3vw, 34px) 94px;
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.65fr);
  gap: 16px;
}

.focus-card, .panel, .search-panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 16px;
  box-shadow: var(--shadow);
}

.focus-card {
  padding: 24px;
  background: linear-gradient(135deg, #ffffff 0%, #eef6f1 100%);
}

.label {
  display: inline-flex;
  margin-bottom: 18px;
  border-radius: 999px;
  padding: 5px 10px;
  background: #dcebe3;
  color: #1c5d4b;
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
}

.action-row { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 20px; }
.primary-action, .ghost-action, .tab, .bottom-nav button {
  border: 0;
  cursor: pointer;
  min-height: 42px;
}

.primary-action {
  border-radius: 999px;
  padding: 10px 16px;
  background: var(--accent);
  color: #fff;
  font-weight: 800;
}

.ghost-action {
  border-radius: 999px;
  padding: 10px 16px;
  background: #f4eee4;
  color: var(--ink);
  font-weight: 700;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.stat {
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #fff;
}

.stat strong { display: block; font-size: 28px; line-height: 1; }
.stat span { color: var(--muted); font-size: 13px; }

.search-panel { margin-top: 16px; padding: 18px; }
.search-panel label { display: block; margin-bottom: 8px; font-weight: 800; }
.search-panel input {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 14px 15px;
  background: #fff;
  color: var(--ink);
  outline: none;
}

.search-panel input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(31, 111, 91, 0.14); }

.chips, .tag-cloud { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.chip, .tag {
  border: 1px solid #cddbd3;
  border-radius: 999px;
  padding: 7px 10px;
  background: var(--soft);
  color: #214438;
  font-size: 13px;
  cursor: pointer;
}

.tab-bar {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 16px 0;
}

.tab {
  flex: 0 0 auto;
  border-radius: 999px;
  padding: 9px 13px;
  background: #efe8dc;
  color: #3b403c;
  font-weight: 800;
}

.tab.active { background: var(--ink); color: #fff; }

.section-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 0.8fr);
  gap: 16px;
  margin-bottom: 16px;
}

.panel { padding: 18px; }
.panel-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.panel-heading span { color: var(--muted); font-size: 13px; }

.compact-list { display: grid; gap: 8px; }
.list-row {
  display: block;
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 11px 12px;
  background: #fff;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.list-row b { display: block; margin-bottom: 2px; }
.list-row span { color: var(--muted); font-size: 13px; }

.card-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.node-card {
  display: flex;
  min-height: 210px;
  flex-direction: column;
  justify-content: space-between;
  border: 1px solid var(--line);
  border-radius: 15px;
  padding: 15px;
  background: #fff;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.node-card:hover { border-color: #a8c5b7; }
.node-type { color: var(--accent-2); font-size: 12px; font-weight: 900; text-transform: uppercase; }
.node-card h3 { margin: 8px 0; font-size: 18px; letter-spacing: 0; }
.node-card p { color: var(--muted); font-size: 14px; }
.meta-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.pill {
  border-radius: 999px;
  padding: 4px 8px;
  background: #f0f3f5;
  color: #3d5261;
  font-size: 12px;
}

.bottom-nav {
  position: fixed;
  right: 12px;
  bottom: 12px;
  left: 12px;
  z-index: 20;
  display: none;
  grid-template-columns: repeat(5, 1fr);
  gap: 6px;
  border: 1px solid rgba(20, 35, 28, 0.12);
  border-radius: 18px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 18px 40px rgba(20, 35, 28, 0.18);
  backdrop-filter: blur(14px);
}

.bottom-nav button {
  border-radius: 12px;
  background: transparent;
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}

.detail-panel {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: none;
}

.detail-panel.open { display: block; }

.detail-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(9, 18, 14, 0.46);
}

.detail-card {
  position: absolute;
  top: 28px;
  right: max(16px, calc((100vw - 860px) / 2));
  bottom: 28px;
  width: min(820px, calc(100vw - 32px));
  overflow: auto;
  border-radius: 18px;
  padding: 22px;
  background: #fff;
  box-shadow: 0 28px 90px rgba(0, 0, 0, 0.28);
}

.detail-close {
  float: right;
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 8px 12px;
  background: #fff;
  cursor: pointer;
}

#detail-meta {
  color: var(--muted);
  font-size: 14px;
}

#detail-body {
  margin-top: 18px;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 16px;
  background: #fbf8f0;
  color: var(--ink);
  font-family: inherit;
  font-size: 15px;
  line-height: 1.65;
}

.empty {
  border: 1px dashed var(--line);
  border-radius: 14px;
  padding: 18px;
  color: var(--muted);
  text-align: center;
}

@media (max-width: 820px) {
  .app-header { display: block; padding-top: 24px; }
  .github-link { display: inline-flex; margin-top: 18px; }
  .hero-grid, .section-grid, .card-grid { grid-template-columns: 1fr; }
  .stats-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .bottom-nav { display: grid; }
  .node-card { min-height: 185px; }
  .detail-card { inset: auto 10px 10px; top: 22px; width: auto; border-radius: 16px; }
}

@media (max-width: 420px) {
  main { padding-inline: 12px; }
  .focus-card, .panel, .search-panel { border-radius: 14px; }
  .stats-grid { grid-template-columns: 1fr 1fr; }
}
""",
        encoding="utf-8",
    )

    (DOCS / "app.js").write_text(
        """const state = {
  data: null,
  filter: "all",
  query: "",
  topic: "",
};

const typeLabels = {
  session: "Session",
  vocabulary: "Vocabulary",
  grammar_error: "Mistake",
  pronunciation: "Pronunciation",
  expression: "Expression",
  mini_response: "Response",
  personal_story: "Story",
};

const $ = (selector) => document.querySelector(selector);

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function relativeLink(path) {
  return `../${path}`;
}

function matchesFilter(node) {
  if (state.filter === "all") return true;
  if (state.filter === "due") {
    const reviewIds = [...state.data.due, ...state.data.upcoming].map((item) => item.id);
    return reviewIds.includes(node.id);
  }
  return node.type === state.filter;
}

function matchesQuery(node) {
  const query = state.query.trim().toLowerCase();
  if (!query && !state.topic) return true;
  const haystack = [
    node.title,
    node.type,
    node.excerpt,
    ...(node.topics || []),
    ...(node.skills || []),
    ...(node.related || []),
  ].join(" ").toLowerCase();
  const queryOk = !query || haystack.includes(query);
  const topicOk = !state.topic || (node.topics || []).includes(state.topic);
  return queryOk && topicOk;
}

function filteredNodes() {
  return state.data.nodes.filter((node) => matchesFilter(node) && matchesQuery(node));
}

function renderStats() {
  const stats = state.data.stats;
  $("#stats").innerHTML = [
    ["Sessions", stats.sessions],
    ["Words", stats.vocabulary],
    ["Mistakes", stats.grammarMistakes],
    ["Responses", stats.responses],
  ].map(([label, count]) => `<div class="stat"><strong>${count}</strong><span>${label}</span></div>`).join("");
}

function renderReview() {
  const due = state.data.due;
  const upcoming = state.data.upcoming.slice(0, 6);
  $("#today-title").textContent = due.length ? `${due.length} item${due.length === 1 ? "" : "s"} due` : "Nothing due today";
  $("#today-copy").textContent = due.length
    ? "Start with review, then browse the linked topics and reusable responses."
    : "No item is due yet. Use the upcoming queue or explore recent nodes.";
  $("#review-count").textContent = `${due.length} due`;
  const rows = [...due, ...upcoming].slice(0, 8);
  $("#review-list").innerHTML = rows.length ? rows.map((node) => `
    <button class="list-row" data-node-id="${escapeHtml(node.id)}">
      <b>${escapeHtml(node.title)}</b>
      <span>${escapeHtml(typeLabels[node.type] || node.type)} - due ${escapeHtml(node.due_date || node.review?.next_due || "")}</span>
    </button>
  `).join("") : `<div class="empty">No review items yet.</div>`;
}

function renderTopics() {
  $("#topic-cloud").innerHTML = state.data.topics.slice(0, 18).map((topic) => `
    <button class="tag" data-topic="${escapeHtml(topic.name)}">${escapeHtml(topic.name)} ${topic.count}</button>
  `).join("");
  $("#quick-filters").innerHTML = state.data.skills.slice(0, 8).map((skill) => `
    <button class="chip" data-query="${escapeHtml(skill.name)}">${escapeHtml(skill.name)}</button>
  `).join("");
}

function renderCards() {
  const nodes = filteredNodes();
  $("#result-count").textContent = `${nodes.length} item${nodes.length === 1 ? "" : "s"}`;
  $("#results-title").textContent = state.topic ? `Topic: ${state.topic}` : "Knowledge nodes";
  $("#cards").innerHTML = nodes.length ? nodes.map((node) => {
    const tags = [...(node.topics || []).slice(0, 2), ...(node.skills || []).slice(0, 1)];
    return `
      <button class="node-card" data-node-id="${escapeHtml(node.id)}">
        <div>
          <span class="node-type">${escapeHtml(typeLabels[node.type] || node.type)}</span>
          <h3>${escapeHtml(node.title)}</h3>
          <p>${escapeHtml(node.excerpt || "Open this node to review details.")}</p>
        </div>
        <div class="meta-row">
          ${tags.map((tag) => `<span class="pill">${escapeHtml(tag)}</span>`).join("")}
        </div>
      </button>
    `;
  }).join("") : `<div class="empty">No matching nodes. Try another search.</div>`;
}

function setFilter(filter) {
  state.filter = filter;
  state.topic = "";
  document.querySelectorAll(".tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.filter === filter);
  });
  renderCards();
}

function openNode(id) {
  const node = state.data.nodes.find((item) => item.id === id) || state.data.upcoming.find((item) => item.id === id);
  if (!node) return;
  $("#detail-type").textContent = typeLabels[node.type] || node.type;
  $("#detail-title").textContent = node.title;
  $("#detail-meta").textContent = `${node.created || "No date"} - ${node.path}`;
  const tags = [...(node.topics || []), ...(node.skills || [])].slice(0, 10);
  $("#detail-tags").innerHTML = tags.map((tag) => `<span class="pill">${escapeHtml(tag)}</span>`).join("");
  $("#detail-body").textContent = node.body || node.excerpt || "No detail available.";
  $("#detail-panel").classList.add("open");
  $("#detail-panel").setAttribute("aria-hidden", "false");
}

function closeDetail() {
  $("#detail-panel").classList.remove("open");
  $("#detail-panel").setAttribute("aria-hidden", "true");
}

function bindEvents() {
  $("#search").addEventListener("input", (event) => {
    state.query = event.target.value;
    renderCards();
  });
  document.addEventListener("click", (event) => {
    const filterButton = event.target.closest("[data-filter]");
    if (filterButton) setFilter(filterButton.dataset.filter);
    const nodeButton = event.target.closest("[data-node-id]");
    if (nodeButton) openNode(nodeButton.dataset.nodeId);
    if (event.target.closest("[data-close-detail]")) closeDetail();
    const topicButton = event.target.closest("[data-topic]");
    if (topicButton) {
      state.topic = topicButton.dataset.topic;
      state.filter = "all";
      document.querySelectorAll(".tab").forEach((button) => button.classList.toggle("active", button.dataset.filter === "all"));
      renderCards();
      window.scrollTo({ top: $("#cards").offsetTop - 80, behavior: "smooth" });
    }
    const queryButton = event.target.closest("[data-query]");
    if (queryButton) {
      $("#search").value = queryButton.dataset.query;
      state.query = queryButton.dataset.query;
      renderCards();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeDetail();
  });
}

async function main() {
  const response = await fetch("data.json", { cache: "no-store" });
  state.data = await response.json();
  renderStats();
  renderReview();
  renderTopics();
  renderCards();
  bindEvents();
}

main().catch((error) => {
  console.error(error);
  $("#cards").innerHTML = `<div class="empty">The knowledge app could not load data.json.</div>`;
});
""",
        encoding="utf-8",
    )


def build(root: Path = ROOT) -> None:
    write_static_assets()
    nodes = iter_nodes()
    today = date.today()
    due, upcoming = due_items(nodes, today)
    stats = {
        "sessions": sum(1 for node in nodes if node["type"] == "session"),
        "vocabulary": sum(1 for node in nodes if node["type"] == "vocabulary"),
        "grammarMistakes": sum(1 for node in nodes if node["type"] == "grammar_error"),
        "expressions": sum(1 for node in nodes if node["type"] == "expression"),
        "responses": sum(1 for node in nodes if node["type"] == "mini_response"),
        "stories": sum(1 for node in nodes if node["type"] == "personal_story"),
        "total": len(nodes),
    }
    payload = {
        "generated": today.isoformat(),
        "stats": stats,
        "topics": group_counts(nodes, "topics"),
        "skills": group_counts(nodes, "skills"),
        "due": due,
        "upcoming": upcoming,
        "nodes": nodes,
    }
    (DOCS / "data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Wrote mobile app: docs/index.html")


def main(argv: list[str]) -> int:
    build(ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
