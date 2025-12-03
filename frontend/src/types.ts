export interface Game {
  id: number;
  steam_id: number;
  name: string;
  app_type?: string;
  short_description?: string;
  header_image_url?: string;
  dimension_1: 'a' | 'b' | 'c' | 'd';
  dimension_2: 'character' | 'unit';
  dimension_3: 'explicit' | 'implied';
  classification_notes?: string;
  developer?: string;
  publisher?: string;
  release_date?: string;
  steam_tags: string[];
  genres: string[];
  last_checked?: string;
  update_count: number;
  last_update?: string;
}

export interface Stats {
  total_games: number;
  total_updates: number;
  recent_updates_30d: number;
  dimension_1: Record<string, number>;
  dimension_2: Record<string, number>;
  dimension_3: Record<string, number>;
  last_updated: string;
}