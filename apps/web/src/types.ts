export type PlayableStatus = 'playable' | 'broken' | 'requires-plugin' | 'unknown';

export type GameEntry = {
  id: string;
  title: string;
  url: string;
  embed_type: 'iframe' | 'external' | 'download';
  thumbnail: string;
  genre: string[];
  tags: string[];
  source_repo: string;
  license: string;
  playable_status: PlayableStatus;
  added_at: string;
  updated_at: string;
  controls?: string[];
  multiplayer?: 'singleplayer' | 'local-multiplayer' | 'online-multiplayer';
};
