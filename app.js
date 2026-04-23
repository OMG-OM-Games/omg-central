const ui = {
  stats: document.getElementById('stats'),
  search: document.getElementById('search'),
  sourceFilter: document.getElementById('sourceFilter'),
  gameList: document.getElementById('gameList'),
  selectedTitle: document.getElementById('selectedTitle'),
  viewer: document.getElementById('viewer'),
  openNewTab: document.getElementById('openNewTab'),
  nextEmbed: document.getElementById('nextEmbed'),
  meta: document.getElementById('meta'),
};

let state = {
  allGames: [],
  filteredGames: [],
  selectedId: null,
  embedIndexById: {},
};

function normalize(s) {
  return (s || '').toLowerCase().trim();
}

function applyFilters() {
  const q = normalize(ui.search.value);
  const src = ui.sourceFilter.value;

  state.filteredGames = state.allGames.filter((g) => {
    const inSource = !src || g.source === src;
    const inText =
      !q ||
      normalize(g.title).includes(q) ||
      normalize(g.path).includes(q) ||
      normalize(g.source).includes(q);
    return inSource && inText;
  });

  renderList();
}

function renderList() {
  ui.gameList.innerHTML = '';

  for (const game of state.filteredGames) {
    const el = document.createElement('button');
    el.className = 'game-item' + (state.selectedId === game.id ? ' active' : '');
    el.innerHTML = `
      <div><strong>${game.title}</strong></div>
      <div class="source">${game.source}</div>
      <div class="source">${game.path}</div>
    `;
    el.onclick = () => selectGame(game.id);
    ui.gameList.appendChild(el);
  }

  if (!state.filteredGames.length) {
    ui.gameList.innerHTML = '<p>No matching games.</p>';
  }
}

function resolveEmbedUrl(game) {
  const urls = (game.fallback_urls && game.fallback_urls.length ? game.fallback_urls : [game.url]).filter(Boolean);
  const idx = state.embedIndexById[game.id] || 0;
  return { url: urls[idx % urls.length], idx, total: urls.length, urls };
}

function selectGame(id) {
  state.selectedId = id;
  const game = state.filteredGames.find((g) => g.id === id) || state.allGames.find((g) => g.id === id);
  if (!game) return;

  const embed = resolveEmbedUrl(game);
  ui.selectedTitle.textContent = `${game.title} — ${game.source}`;
  ui.openNewTab.href = embed.url;
  ui.viewer.src = embed.url;
  ui.meta.textContent = JSON.stringify({
    source: game.source,
    path: game.path,
    default_branch: game.default_branch,
    kind: game.kind || 'game',
    repo_url: game.repo_url || null,
    embed_url: embed.url,
    embed_index: embed.idx + 1,
    embed_total: embed.total,
    fallback_urls: embed.urls,
  }, null, 2);

  renderList();
}

function hydrateSourceFilter(games) {
  const sources = [...new Set(games.map((g) => g.source))].sort((a, b) => a.localeCompare(b));
  for (const source of sources) {
    const opt = document.createElement('option');
    opt.value = source;
    opt.textContent = source;
    ui.sourceFilter.appendChild(opt);
  }
}

async function init() {
  const res = await fetch('./data/games.json');
  if (!res.ok) {
    ui.stats.textContent = `Failed to load catalog (${res.status})`;
    return;
  }

  const payload = await res.json();
  state.allGames = payload.games || [];
  state.filteredGames = [...state.allGames];

  ui.stats.textContent = `${payload.game_count ?? state.allGames.length} games from ${payload.source_count ?? '?'} sources (generated ${payload.generated_at ?? 'unknown'})`;

  hydrateSourceFilter(state.allGames);
  renderList();

  if (state.filteredGames.length) {
    selectGame(state.filteredGames[0].id);
  }

  ui.search.addEventListener('input', applyFilters);
  ui.sourceFilter.addEventListener('change', applyFilters);
  ui.nextEmbed.addEventListener('click', () => {
    const game = state.allGames.find((g) => g.id === state.selectedId);
    if (!game) return;
    const urls = (game.fallback_urls && game.fallback_urls.length ? game.fallback_urls : [game.url]).filter(Boolean);
    state.embedIndexById[game.id] = ((state.embedIndexById[game.id] || 0) + 1) % urls.length;
    selectGame(game.id);
  });
}

init().catch((err) => {
  console.error(err);
  ui.stats.textContent = 'Failed to initialize app. See console.';
});
