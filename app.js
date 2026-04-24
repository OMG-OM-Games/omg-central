'use strict';

// ── Category metadata ───────────────────────────────────────────────────────
const CAT = {
  all:         { label: 'All Games',   color: '#7c3aed', emoji: '🎮' },
  action:      { label: 'Action',      color: '#ef4444', emoji: '⚡' },
  adventure:   { label: 'Adventure',   color: '#fb923c', emoji: '🗺️' },
  horror:      { label: 'Horror',      color: '#8b5cf6', emoji: '👻' },
  idle:        { label: 'Idle',        color: '#84cc16', emoji: '💰' },
  multiplayer: { label: 'Multiplayer', color: '#ec4899', emoji: '👥' },
  music:       { label: 'Music',       color: '#14b8a6', emoji: '🎵' },
  platformer:  { label: 'Platformer',  color: '#f97316', emoji: '🏃' },
  puzzle:      { label: 'Puzzle',      color: '#06b6d4', emoji: '🧩' },
  racing:      { label: 'Racing',      color: '#f59e0b', emoji: '🏎️' },
  rpg:         { label: 'RPG',         color: '#a855f7', emoji: '⚔️' },
  shooter:     { label: 'Shooter',     color: '#f43f5e', emoji: '🔫' },
  sports:      { label: 'Sports',      color: '#10b981', emoji: '🏀' },
  strategy:    { label: 'Strategy',    color: '#3b82f6', emoji: '♟️' },
  other:       { label: 'Other',       color: '#64748b', emoji: '✨' },
};

// ── State ───────────────────────────────────────────────────────────────────
let activeCat  = 'all';
let searchTerm = '';

// ── DOM refs ────────────────────────────────────────────────────────────────
const $  = id => document.getElementById(id);
const grid     = $('grid');
const empty    = $('empty');
const overlay  = $('overlay');
const frame    = $('game-frame');
const loader   = $('loader');
const catBar   = $('cat-bar');
const searchEl = $('search');
const clearBtn = $('search-clear');

// ── Category bar ────────────────────────────────────────────────────────────
function buildCatBar() {
  const counts = {};
  GAMES.forEach(g => { counts[g.cat] = (counts[g.cat] || 0) + 1; });

  catBar.innerHTML = Object.entries(CAT).map(([id, m]) => {
    const n = id === 'all' ? GAMES.length : (counts[id] || 0);
    if (id !== 'all' && !n) return '';
    return `<button class="cat-pill${id === 'all' ? ' active' : ''}" data-cat="${id}">
      <span class="cat-pill-emoji">${m.emoji}</span>
      <span>${m.label}</span>
      <span class="cat-pill-count">${n}</span>
    </button>`;
  }).join('');

  catBar.addEventListener('click', e => {
    const btn = e.target.closest('.cat-pill');
    if (!btn) return;
    catBar.querySelectorAll('.cat-pill').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeCat = btn.dataset.cat;
    render();
  });
}

// ── Game grid ───────────────────────────────────────────────────────────────
function render() {
  const lower = searchTerm.toLowerCase();
  const list  = GAMES.filter(g =>
    (activeCat === 'all' || g.cat === activeCat) &&
    (!lower || g.name.toLowerCase().includes(lower))
  );

  const n = list.length;
  $('header-count').textContent = `${n} game${n === 1 ? '' : 's'}`;

  if (!n) {
    grid.innerHTML = '';
    empty.classList.remove('hidden');
    return;
  }

  empty.classList.add('hidden');

  grid.innerHTML = list.map(g => {
    const m   = CAT[g.cat];
    const idx = GAMES.indexOf(g);
    const bg  = `linear-gradient(145deg, ${m.color}2e 0%, ${m.color}0a 100%)`;
    return `<div class="card" data-idx="${idx}" title="${g.name}">
      <div class="card-thumb" style="background:${bg}">
        ${g.thumb
          ? `<img src="${g.thumb}" alt="${g.name}" loading="lazy">`
          : `<span class="card-emoji">${m.emoji}</span>`
        }
        <div class="card-play">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="12" r="10" fill="rgba(255,255,255,.15)"/>
            <polygon points="10,8 16,12 10,16" fill="white"/>
          </svg>
        </div>
      </div>
      <div class="card-body">
        <div class="card-name">${g.name}</div>
        <span class="cat-badge" style="background:${m.color}20;color:${m.color}">${m.label}</span>
      </div>
    </div>`;
  }).join('');
}

// Delegated click — attached once
grid.addEventListener('click', e => {
  const card = e.target.closest('.card');
  if (card) openGame(+card.dataset.idx);
});

// ── Game loading ─────────────────────────────────────────────────────────────
function openGame(idx) {
  const g = GAMES[idx];
  const m = CAT[g.cat];

  $('overlay-name').textContent = g.name;
  const badge = $('overlay-badge');
  badge.textContent      = m.label;
  badge.style.background = m.color + '22';
  badge.style.color      = m.color;

  overlay.classList.remove('hidden');
  loader.style.display = 'flex';
  frame.style.opacity  = '0';
  frame.src = '';

  // Load directly — iframe runs in the game's own origin so same-origin
  // fetches (Unity data files, Construct 2 assets, etc.) are never blocked by CORS
  frame.onload = () => {
    loader.style.display = 'none';
    frame.style.opacity  = '1';
  };
  frame.src = g.url;
}

function closeGame() {
  overlay.classList.add('hidden');
  frame.src = '';
  loader.style.display = 'none';
  frame.style.opacity  = '0';
}

function goFullscreen() {
  const el = frame;
  (el.requestFullscreen || el.webkitRequestFullscreen || el.mozRequestFullScreen
    || function(){}).call(el);
}

// ── Search ──────────────────────────────────────────────────────────────────
searchEl.addEventListener('input', e => {
  searchTerm = e.target.value;
  clearBtn.classList.toggle('hidden', !searchTerm);
  render();
});

clearBtn.addEventListener('click', () => {
  searchEl.value = '';
  searchTerm = '';
  clearBtn.classList.add('hidden');
  searchEl.focus();
  render();
});

// ── Controls ────────────────────────────────────────────────────────────────
$('close-btn').addEventListener('click', closeGame);
$('fs-btn').addEventListener('click', goFullscreen);

document.addEventListener('keydown', e => {
  if (!overlay.classList.contains('hidden')) {
    if (e.key === 'Escape') closeGame();
    if (e.key === 'f' || e.key === 'F') goFullscreen();
  }
});

// ── Boot ────────────────────────────────────────────────────────────────────
buildCatBar();
render();
