'use strict';

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

let activeCat  = 'all';
let searchTerm = '';

// ── Build category nav ──────────────────────────────────────────────────────
function buildNav() {
  const counts = {};
  GAMES.forEach(g => { counts[g.cat] = (counts[g.cat] || 0) + 1; });

  const nav = document.getElementById('cat-nav');
  nav.innerHTML = Object.entries(CAT).map(([id, m]) => {
    const n = id === 'all' ? GAMES.length : (counts[id] || 0);
    if (id !== 'all' && !n) return '';
    return `<button class="cat-btn${id === 'all' ? ' active' : ''}" data-cat="${id}">
      <span class="cat-dot" style="background:${m.color}"></span>
      <span class="cat-name">${m.label}</span>
      <span class="cat-num">${n}</span>
    </button>`;
  }).join('');

  nav.addEventListener('click', e => {
    const btn = e.target.closest('.cat-btn');
    if (!btn) return;
    nav.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeCat = btn.dataset.cat;
    render();
  });
}

// ── Render game grid ────────────────────────────────────────────────────────
function render() {
  const lower = searchTerm.toLowerCase();
  const list  = GAMES.filter(g =>
    (activeCat === 'all' || g.cat === activeCat) &&
    (!lower || g.name.toLowerCase().includes(lower))
  );

  const grid  = document.getElementById('grid');
  const empty = document.getElementById('empty');
  const count = document.getElementById('count-label');

  count.textContent = list.length
    ? `${list.length} game${list.length === 1 ? '' : 's'}`
    : '0 games';

  if (!list.length) {
    grid.innerHTML = '';
    empty.classList.remove('hidden');
    return;
  }

  empty.classList.add('hidden');
  grid.innerHTML = list.map(g => {
    const m   = CAT[g.cat];
    const idx = GAMES.indexOf(g);
    const bg  = `linear-gradient(135deg, ${m.color}30 0%, ${m.color}0c 100%)`;
    return `<div class="card" data-idx="${idx}" data-cat="${g.cat}" title="${g.name}">
      <div class="card-thumb" style="background:${bg}">
        ${g.thumb
          ? `<img src="${g.thumb}" alt="${g.name}" loading="lazy">`
          : `<span class="card-emoji">${m.emoji}</span>`
        }
      </div>
      <div class="card-body">
        <div class="card-name">${g.name}</div>
        <span class="cat-badge" style="background:${m.color}20;color:${m.color}">${m.label}</span>
      </div>
    </div>`;
  }).join('');
}

// ── Open game in overlay ────────────────────────────────────────────────────
function openGame(idx) {
  const g   = GAMES[idx];
  const m   = CAT[g.cat];
  const frame   = document.getElementById('game-frame');
  const loading = document.getElementById('loading');
  const overlay = document.getElementById('overlay');

  document.getElementById('overlay-title').textContent = g.name;

  const badge = document.getElementById('overlay-badge');
  badge.textContent        = m.label;
  badge.style.background   = m.color + '22';
  badge.style.color        = m.color;

  loading.style.display = 'flex';
  frame.style.opacity   = '0';
  frame.src             = g.url;

  frame.onload = () => {
    loading.style.display = 'none';
    frame.style.opacity   = '1';
  };

  overlay.classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeOverlay() {
  document.getElementById('overlay').classList.add('hidden');
  document.getElementById('game-frame').src = '';
  document.getElementById('loading').style.display = 'none';
  document.body.style.overflow = '';
}

function goFullscreen() {
  const el = document.getElementById('game-frame');
  if      (el.requestFullscreen)       el.requestFullscreen();
  else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen();
}

// ── Init ────────────────────────────────────────────────────────────────────
function init() {
  buildNav();
  render();

  document.getElementById('search').addEventListener('input', e => {
    searchTerm = e.target.value;
    render();
  });

  // Delegated click on grid — attached once
  document.getElementById('grid').addEventListener('click', e => {
    const card = e.target.closest('.card');
    if (card) openGame(+card.dataset.idx);
  });

  document.getElementById('back-btn').addEventListener('click', closeOverlay);
  document.getElementById('fullscreen-btn').addEventListener('click', goFullscreen);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeOverlay(); });
}

init();
