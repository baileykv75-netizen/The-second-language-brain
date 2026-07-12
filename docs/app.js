const state = {
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
    ["Expressions", stats.expressions],
  ].map(([label, count]) => `<div class="stat"><strong>${count}</strong><span>${label}</span></div>`).join("");
}

function renderReview() {
  const due = state.data.due;
  const upcoming = state.data.upcoming.slice(0, 6);
  $("#today-title").textContent = due.length ? `${due.length} item${due.length === 1 ? "" : "s"} due` : "Nothing due today";
  $("#today-copy").textContent = due.length
    ? "Start with review, then browse the linked topics and expressions."
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
