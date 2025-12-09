export type Platform = 'steam' | 'battlenet' | 'gog' | 'epic' | 'itchio' | 'manual';

export interface Game {
  id: number;
  steam_id?: number;
  battlenet_id?: string;
  battlenet_store_id?: string;  // Store page slug if different from battlenet_id
  gog_id?: string;
  epic_id?: string;
  itchio_id?: string;
  platforms: Platform[];
  primary_platform: Platform;
  external_url?: string;
  name: string;
  app_type?: string;
  short_description?: string;
  header_image_url?: string;
  dimension_1: 'a' | 'b' | 'c' | 'd';
  dimension_2: 'character' | 'unit';
  dimension_3: 'explicit' | 'implied';
  dimension_1_notes?: string;
  dimension_2_notes?: string;
  dimension_3_notes?: string;
  date_updated?: string;
  developer?: string;
  publisher?: string;
  release_date?: string;
  price_usd?: number;
  price_notes?: string | null;
  steam_tags: string[];
  genres: string[];
  last_checked?: string;
  update_count: number;
  last_update?: string;
  last_update_url?: string;
  last_update_title?: string;
  last_announcement?: string;
  last_announcement_url?: string;
  last_announcement_title?: string;
}

// Platform display info
export const PLATFORM_INFO: Record<Platform, { name: string; color: string; icon: string }> = {
  steam: { name: 'Steam', color: '#1b2838', icon: '🎮' },
  battlenet: { name: 'Battle.net', color: '#00aeff', icon: '⚔️' },
  gog: { name: 'GOG', color: '#86328a', icon: '🎁' },
  epic: { name: 'Epic Games', color: '#2a2a2a', icon: '🏰' },
  itchio: { name: 'itch.io', color: '#fa5c5c', icon: '🎲' },
  manual: { name: 'Other', color: '#666666', icon: '🔗' },
};

// Generate store URLs for each platform
export function getStoreUrl(game: Game, platform: Platform): string | null {
  switch (platform) {
    case 'steam':
      return game.steam_id ? `https://store.steampowered.com/app/${game.steam_id}` : null;
    case 'battlenet': {
      // Use battlenet_store_id if available (for cases like WoW where API slug differs from store slug)
      const storeSlug = game.battlenet_store_id || game.battlenet_id;
      return storeSlug ? `https://shop.battle.net/product/${storeSlug}` : null;
    }
    case 'gog':
      return game.gog_id ? `https://www.gog.com/game/${game.gog_id}` : null;
    case 'epic':
      return game.epic_id ? `https://store.epicgames.com/p/${game.epic_id}` : null;
    case 'itchio':
      return game.itchio_id ? `https://itch.io/games/${game.itchio_id}` : null;
    case 'manual':
      return game.external_url || null;
    default:
      return null;
  }
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