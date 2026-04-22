import { useMemo, useRef, useState } from 'react';
import Fuse from 'fuse.js';
import { useVirtualizer } from '@tanstack/react-virtual';
import { catalogEntries } from './catalog';
import type { GameEntry } from './types';

type MenuItem = 'Home' | 'Categories' | 'New' | 'Popular' | 'Random' | 'Sources';

type FilterState = {
  genre: string;
  source: string;
  tags: string;
  controls: string;
  multiplayer: string;
  status: string;
};

const menuItems: MenuItem[] = ['Home', 'Categories', 'New', 'Popular', 'Random', 'Sources'];

function uniqueValues<T>(selector: (item: GameEntry) => T[]): string[] {
  return Array.from(new Set(catalogEntries.flatMap(selector).map(String))).sort((a, b) => a.localeCompare(b));
}

const options = {
  genres: uniqueValues((x) => x.genre),
  sources: Array.from(new Set(catalogEntries.map((x) => x.source_repo))).sort((a, b) => a.localeCompare(b)),
  tags: uniqueValues((x) => x.tags),
  controls: uniqueValues((x) => x.controls ?? []),
  multiplayer: Array.from(new Set(catalogEntries.map((x) => x.multiplayer).filter(Boolean) as string[])).sort((a, b) =>
    a.localeCompare(b)
  ),
  status: Array.from(new Set(catalogEntries.map((x) => x.playable_status))).sort((a, b) => a.localeCompare(b))
};

const fuse = new Fuse(catalogEntries, {
  includeScore: true,
  threshold: 0.35,
  keys: ['title', 'id', 'tags', 'genre', 'source_repo']
});

function applyFilters(entries: GameEntry[], filters: FilterState): GameEntry[] {
  return entries.filter((entry) => {
    const isGenreMatch = !filters.genre || entry.genre.includes(filters.genre);
    const isSourceMatch = !filters.source || entry.source_repo === filters.source;
    const isTagsMatch = !filters.tags || entry.tags.includes(filters.tags);
    const isControlsMatch = !filters.controls || (entry.controls ?? []).includes(filters.controls);
    const isMultiplayerMatch = !filters.multiplayer || entry.multiplayer === filters.multiplayer;
    const isStatusMatch = !filters.status || entry.playable_status === filters.status;

    return isGenreMatch && isSourceMatch && isTagsMatch && isControlsMatch && isMultiplayerMatch && isStatusMatch;
  });
}

export default function App() {
  const [activeMenu, setActiveMenu] = useState<MenuItem>('Home');
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<FilterState>({
    genre: '',
    source: '',
    tags: '',
    controls: '',
    multiplayer: '',
    status: ''
  });

  const searchedEntries = useMemo(() => {
    if (!query.trim()) return catalogEntries;
    return fuse.search(query).map((result) => result.item);
  }, [query]);

  const filteredEntries = useMemo(() => applyFilters(searchedEntries, filters), [searchedEntries, filters]);

  const parentRef = useRef<HTMLDivElement>(null);
  const rowVirtualizer = useVirtualizer({
    count: filteredEntries.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 108,
    overscan: 10
  });

  return (
    <div className="layout">
      <header className="top-menu">
        <h1>OMG Central</h1>
        <nav>
          {menuItems.map((item) => (
            <button key={item} onClick={() => setActiveMenu(item)} className={activeMenu === item ? 'active' : ''}>
              {item}
            </button>
          ))}
        </nav>
      </header>
      <div className="content-wrap">
        <aside className="filters">
          <h2>Filters</h2>
          <FilterSelect
            label="Genre"
            value={filters.genre}
            options={options.genres}
            onChange={(value) => setFilters((prev) => ({ ...prev, genre: value }))}
          />
          <FilterSelect
            label="Source"
            value={filters.source}
            options={options.sources}
            onChange={(value) => setFilters((prev) => ({ ...prev, source: value }))}
          />
          <FilterSelect
            label="Tags"
            value={filters.tags}
            options={options.tags}
            onChange={(value) => setFilters((prev) => ({ ...prev, tags: value }))}
          />
          <FilterSelect
            label="Controls"
            value={filters.controls}
            options={options.controls}
            onChange={(value) => setFilters((prev) => ({ ...prev, controls: value }))}
          />
          <FilterSelect
            label="Multiplayer"
            value={filters.multiplayer}
            options={options.multiplayer}
            onChange={(value) => setFilters((prev) => ({ ...prev, multiplayer: value }))}
          />
          <FilterSelect
            label="Status"
            value={filters.status}
            options={options.status}
            onChange={(value) => setFilters((prev) => ({ ...prev, status: value }))}
          />
        </aside>
        <main className="catalog">
          <div className="catalog-header">
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search by title, tags, source…"
              type="search"
            />
            <small>
              {filteredEntries.length} / {catalogEntries.length} entries
            </small>
          </div>
          <div ref={parentRef} className="virtual-list">
            <div style={{ height: `${rowVirtualizer.getTotalSize()}px`, position: 'relative' }}>
              {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                const item = filteredEntries[virtualRow.index];
                return (
                  <article
                    key={item.id}
                    className="game-card"
                    style={{ transform: `translateY(${virtualRow.start}px)` }}
                  >
                    <img src={item.thumbnail} alt={item.title} loading="lazy" />
                    <div>
                      <a href={item.url} target="_blank" rel="noreferrer">
                        {item.title}
                      </a>
                      <p>{item.tags.join(' • ')}</p>
                      <p className="meta">
                        {item.genre.join(', ')} · {item.playable_status} · {item.source_repo}
                      </p>
                    </div>
                  </article>
                );
              })}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label>
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">All</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}
