const PAGE_SIZE = 48;

const state = {
  allGames: [],
  filteredGames: [],
  page: 1,
  filters: {
    search: "",
    source: "all",
    status: "all",
    category: "all",
  },
};

const searchInput = document.querySelector("#searchInput");
const sourceFilter = document.querySelector("#sourceFilter");
const statusFilter = document.querySelector("#statusFilter");
const categoryFilter = document.querySelector("#categoryFilter");
const gameGrid = document.querySelector("#gameGrid");
const stats = document.querySelector("#stats");
const pageLabel = document.querySelector("#pageLabel");
const prevBtn = document.querySelector("#prevBtn");
const nextBtn = document.querySelector("#nextBtn");

function unique(values) {
  return [...new Set(values)].sort((a, b) => a.localeCompare(b));
}

function option(value, label = value) {
  const el = document.createElement("option");
  el.value = value;
  el.textContent = label;
  return el;
}

function hydrateFilters(games) {
  const sources = unique(games.map((g) => g.sourceId));
  const categories = unique(games.map((g) => g.category));

  sources.forEach((source) => {
    sourceFilter.appendChild(option(source));
  });

  categories.forEach((category) => {
    categoryFilter.appendChild(option(category));
  });
}

function applyFilters() {
  const search = state.filters.search.trim().toLowerCase();

  state.filteredGames = state.allGames.filter((game) => {
    if (state.filters.source !== "all" && game.sourceId !== state.filters.source) {
      return false;
    }

    if (state.filters.status !== "all" && game.status !== state.filters.status) {
      return false;
    }

    if (state.filters.category !== "all" && game.category !== state.filters.category) {
      return false;
    }

    if (!search) {
      return true;
    }

    const haystack = [game.title, game.sourceName, game.category, ...(game.tags || [])]
      .join(" ")
      .toLowerCase();

    return haystack.includes(search);
  });

  state.page = 1;
  render();
}

function gameCard(game) {
  const card = document.createElement("article");
  card.className = "game-card";

  const title = document.createElement("h3");
  title.textContent = game.title;

  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = `${game.sourceName} • ${game.category}`;

  const badge = document.createElement("span");
  badge.className = `badge ${game.status}`;
  badge.textContent = game.status;

  const notes = document.createElement("div");
  notes.className = "meta";
  notes.textContent = game.notes || "";

  card.append(title, meta, badge, notes);
  return card;
}

function render() {
  const total = state.filteredGames.length;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  state.page = Math.min(state.page, pageCount);

  const start = (state.page - 1) * PAGE_SIZE;
  const pageRows = state.filteredGames.slice(start, start + PAGE_SIZE);

  gameGrid.replaceChildren(...pageRows.map(gameCard));

  const verified = state.filteredGames.filter((g) => g.status === "verified").length;
  stats.textContent = `Showing ${pageRows.length} of ${total} games (verified: ${verified}). Total catalog loaded: ${state.allGames.length}.`;

  pageLabel.textContent = `Page ${state.page} / ${pageCount}`;
  prevBtn.disabled = state.page <= 1;
  nextBtn.disabled = state.page >= pageCount;
}

function attachEvents() {
  searchInput.addEventListener("input", (event) => {
    state.filters.search = event.target.value;
    applyFilters();
  });

  sourceFilter.addEventListener("change", (event) => {
    state.filters.source = event.target.value;
    applyFilters();
  });

  statusFilter.addEventListener("change", (event) => {
    state.filters.status = event.target.value;
    applyFilters();
  });

  categoryFilter.addEventListener("change", (event) => {
    state.filters.category = event.target.value;
    applyFilters();
  });

  prevBtn.addEventListener("click", () => {
    state.page = Math.max(1, state.page - 1);
    render();
  });

  nextBtn.addEventListener("click", () => {
    state.page += 1;
    render();
  });
}

async function init() {
  const response = await fetch("data/games.json");
  const games = await response.json();

  state.allGames = games;
  hydrateFilters(games);
  attachEvents();
  applyFilters();
}

init().catch((error) => {
  stats.textContent = `Failed to load catalog: ${error.message}`;
});
