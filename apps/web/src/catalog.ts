import type { GameEntry } from './types';

const modules = import.meta.glob('../../../data/games/*.json', {
  eager: true,
  import: 'default'
}) as Record<string, GameEntry>;

export const catalogEntries: GameEntry[] = Object.entries(modules)
  .filter(([path]) => !path.endsWith('/index.json'))
  .map(([, value]) => value)
  .sort((a, b) => a.title.localeCompare(b.title));
