import { useMemo, useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  flexRender,
} from '@tanstack/react-table';
import type { ColumnDef, FilterFn, SortingFn } from '@tanstack/react-table';
import type { Game, Platform } from '../types';
import { PLATFORM_INFO, getStoreUrl } from '../types';
import SubmissionForm from './SubmissionForm';
import FilterPanel, {
  type FilterState,
  initialFilterState,
  countActiveFilters,
} from './FilterPanel';

// SVG icon components for each platform
function SteamIcon({ className }: { className?: string }) {
  return <img src="/icons/steam.svg" alt="Steam" className={className} />;
}

function BattlenetIcon({ className }: { className?: string }) {
  return <img src="/icons/battlenet.svg" alt="Battle.net" className={`${className} invert`} />;
}

// Generic platform icon with tooltip (matches CellTooltip style)
function PlatformIconWithTooltip({
  platform,
  url,
  flipToBottom = false
}: {
  platform: Platform;
  url: string | null;
  flipToBottom?: boolean;
}) {
  const info = PLATFORM_INFO[platform];
  if (!info) return null;

  const iconClass = "w-5 h-5";

  const renderIcon = () => {
    switch (platform) {
      case 'steam':
        return <SteamIcon className={iconClass} />;
      case 'battlenet':
        return <BattlenetIcon className={iconClass} />;
      default:
        return <span className="text-base">{info.icon}</span>;
    }
  };

  const tooltipText = url ? `View on ${info.name}` : info.name;

  const tooltipContent = flipToBottom ? (
    <div className="pointer-events-none absolute top-full left-1/2 -translate-x-1/2 mt-2 px-2 py-1 text-xs text-gray-200 bg-gray-900 border border-purple-700/50 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 shadow-xl">
      {tooltipText}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-gray-900"></div>
    </div>
  ) : (
    <div className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 text-xs text-gray-200 bg-gray-900 border border-purple-700/50 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 shadow-xl">
      {tooltipText}
      <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
    </div>
  );

  if (url) {
    return (
      <div className="group relative inline-block">
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="hover:scale-110 transition-transform cursor-pointer block"
          onClick={(e) => e.stopPropagation()}
        >
          {renderIcon()}
        </a>
        {tooltipContent}
      </div>
    );
  }

  return (
    <div className="group relative inline-block">
      <span className="opacity-50 block">{renderIcon()}</span>
      {tooltipContent}
    </div>
  );
}

// Platform icons component - shows clickable icons for each platform a game is on
function PlatformIcons({ game, flipToBottom = false }: { game: Game; flipToBottom?: boolean }) {
  return (
    <div className="flex gap-1.5 items-center">
      {game.platforms.map((platform) => (
        <PlatformIconWithTooltip
          key={platform}
          platform={platform as Platform}
          url={getStoreUrl(game, platform as Platform)}
          flipToBottom={flipToBottom}
        />
      ))}
    </div>
  );
}

interface GamesTableProps {
  games: Game[];
}

// Tooltip descriptions for taxonomy columns
const TAXONOMY_INFO = {
  centrality: {
    title: 'Centrality',
    description: 'How central necromancy is to the gameplay experience',
    values: [
      { key: 'a', label: 'Core', color: 'text-green-400', description: 'Necromancy is central to the character or unit\'s identity and gameplay' },
      { key: 'b', label: 'Dedicated Spec', color: 'text-blue-400', description: 'Cohesive set of necromantic skills or equipment available to specialize into' },
      { key: 'c', label: 'Isolated', color: 'text-yellow-400', description: 'One or more necromantic skills or equipment exist, but are not grouped into a cohesive category' },
      { key: 'd', label: 'Minimal', color: 'text-gray-400', description: 'The character/unit may possess necromantic capabilities by technicality or in lore, but with minimal impact to their identity or gameplay' },
    ],
  },
  pov: {
    title: 'POV',
    description: 'The player\'s relationship to the necromancer',
    values: [
      { key: 'character', label: 'Character', color: 'text-purple-300', description: 'Play AS the necromancer (who may control other necromancers)' },
      { key: 'unit', label: 'Unit', color: 'text-purple-300', description: 'Play as some entity controlling one or more necromancers, but not as any of them' },
    ],
  },
  naming: {
    title: 'Naming',
    description: 'Whether necromancy is explicitly named in the game',
    values: [
      { key: 'explicit', label: 'Explicit', color: 'text-green-300', description: 'An exact or minor variant of "necromancer" or "necromancy" used in game' },
      { key: 'implied', label: 'Implied', color: 'text-blue-300', description: 'Necromancy not mentioned by name in game' },
    ],
  },
};

// Centrality sort order: Higher = better (Core at top when sorting descending)
// a (Core) = 3, b (Dedicated Spec) = 2, c (Isolated) = 1, d (Minimal) = 0
const centralitySortOrder: Record<string, number> = { a: 3, b: 2, c: 1, d: 0 };

const centralitySortFn: SortingFn<Game> = (rowA, rowB, columnId) => {
  const a = rowA.getValue(columnId) as string;
  const b = rowB.getValue(columnId) as string;
  return centralitySortOrder[a] - centralitySortOrder[b];
};

// Helper to normalize strings for matching
const normalize = (str: string) => str.toLowerCase().replace(/[®©™]/g, '');

// Combined filter value type (search + filters encoded together)
interface CombinedFilterValue {
  search: string;
  filters: FilterState;
}

// Filter function that handles both search and advanced filters
const combinedFilterFn: FilterFn<Game> = (row, _columnId, filterValue: CombinedFilterValue) => {
  const game = row.original;
  const { search, filters } = filterValue;

  // Global search filter (from search bar)
  if (search) {
    const searchLower = search.toLowerCase();
    const matchesSearch =
      normalize(game.name).includes(searchLower) ||
      (game.developer && normalize(game.developer).includes(searchLower));
    if (!matchesSearch) return false;
  }

  // Genres filter (OR logic - match any selected genre)
  if (filters.genres.length > 0) {
    const hasMatchingGenre = filters.genres.some((g) => game.genres.includes(g));
    if (!hasMatchingGenre) return false;
  }

  // Platforms filter (OR logic - match any selected platform)
  if (filters.platforms.length > 0) {
    const hasMatchingPlatform = filters.platforms.some((p) => game.platforms.includes(p));
    if (!hasMatchingPlatform) return false;
  }

  // Announcement date range filter
  if (filters.announcementDateFrom && game.last_announcement) {
    const announcementDate = new Date(game.last_announcement);
    const fromDate = new Date(filters.announcementDateFrom);
    if (announcementDate < fromDate) return false;
  }
  if (filters.announcementDateTo && game.last_announcement) {
    const announcementDate = new Date(game.last_announcement);
    const toDate = new Date(filters.announcementDateTo);
    toDate.setHours(23, 59, 59, 999); // Include the entire day
    if (announcementDate > toDate) return false;
  }

  // Last updated date range filter
  if (filters.lastUpdatedFrom && game.last_update) {
    const updateDate = new Date(game.last_update);
    const fromDate = new Date(filters.lastUpdatedFrom);
    if (updateDate < fromDate) return false;
  }
  if (filters.lastUpdatedTo && game.last_update) {
    const updateDate = new Date(game.last_update);
    const toDate = new Date(filters.lastUpdatedTo);
    toDate.setHours(23, 59, 59, 999); // Include the entire day
    if (updateDate > toDate) return false;
  }

  // Price range filter
  if (filters.priceMin) {
    const minPrice = parseFloat(filters.priceMin);
    const gamePrice = game.price_usd ?? 0;
    if (gamePrice < minPrice) return false;
  }
  if (filters.priceMax) {
    const maxPrice = parseFloat(filters.priceMax);
    const gamePrice = game.price_usd ?? 0;
    if (gamePrice > maxPrice) return false;
  }

  // Early Access filter (exclude if not checked, unless game has no genres/tags)
  if (!filters.includeEarlyAccess) {
    const hasEarlyAccess = game.genres.includes('Early Access') || game.steam_tags?.includes('Early Access');
    // Only exclude if the game actually has tags/genres and includes Early Access
    if (hasEarlyAccess && game.genres.length > 0) return false;
  }

  // Necromancy grid filter (only applies if not all 16 are selected)
  if (filters.necromancyGrid.length > 0 && filters.necromancyGrid.length < 16) {
    const matchesNecromancy = filters.necromancyGrid.some(
      (f) =>
        game.dimension_1 === f.centrality &&
        game.dimension_2 === f.pov &&
        game.dimension_3 === f.naming
    );
    if (!matchesNecromancy) return false;
  }

  return true;
};

// Wrapper for linked content with mobile-friendly tooltip behavior
function LinkedCellWithTooltip({
  date,
  url,
  title,
  flipToBottom = false,
}: {
  date: string;
  url?: string;
  title?: string;
  flipToBottom?: boolean;
}) {
  const [isOpen, setIsOpen] = useState(false);

  const handleTouch = (e: React.TouchEvent) => {
    if (title || url) {
      e.preventDefault();
      e.stopPropagation();
      setIsOpen(true);
    }
  };

  const handleClick = (e: React.MouseEvent) => {
    // On touch devices, prevent default navigation
    if ('ontouchstart' in window && (title || url)) {
      e.preventDefault();
      e.stopPropagation();
      setIsOpen(true);
    }
    // On desktop, let the link work normally
  };

  // Format the date
  let formatted: string;
  try {
    formatted = new Date(date).toLocaleDateString();
  } catch {
    formatted = date;
  }

  const content = (
    <span
      className={`text-xs ${url ? 'text-gray-400 hover:text-purple-300 hover:underline cursor-pointer' : 'text-gray-500'} transition-colors inline-flex items-center gap-1`}
    >
      {formatted}
      {/* Mobile link indicator */}
      {url && (
        <svg className="w-3 h-3 sm:hidden opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
      )}
    </span>
  );

  if (!title && !url) {
    return content;
  }

  return (
    <div className="group relative inline-block">
      {/* Touch/click handler */}
      <div onTouchStart={handleTouch} onClick={handleClick}>
        {/* Desktop: regular link behavior */}
        {url ? (
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:inline-flex items-center gap-1 text-xs text-gray-400 hover:text-purple-300 hover:underline transition-colors"
            onClick={(e) => e.stopPropagation()}
          >
            {formatted}
          </a>
        ) : (
          <span className="hidden sm:inline text-xs text-gray-500">{formatted}</span>
        )}
        {/* Mobile: just show the date with icon */}
        <span className="sm:hidden inline-flex items-center gap-1 text-xs text-gray-400">
          {formatted}
          {url && (
            <svg className="w-3 h-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          )}
        </span>
      </div>

      {/* Desktop hover tooltip (only if there's a title) */}
      {title && (
        flipToBottom ? (
          <div className="hidden sm:block pointer-events-none absolute top-full left-1/2 -translate-x-1/2 mt-2 px-3 py-2 text-xs text-gray-200 bg-gray-900 border border-purple-700/50 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-normal w-64 text-center z-50 shadow-xl">
            {title}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-gray-900"></div>
          </div>
        ) : (
          <div className="hidden sm:block pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 text-xs text-gray-200 bg-gray-900 border border-purple-700/50 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-normal w-64 text-center z-50 shadow-xl">
            {title}
            <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
          </div>
        )
      )}

      {/* Mobile tap tooltip */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
            onTouchStart={() => setIsOpen(false)}
          />
          <div className={`absolute left-1/2 -translate-x-1/2 px-3 py-2 text-xs text-gray-200 bg-gray-900 border border-purple-700/50 rounded-lg z-50 shadow-xl w-64 ${flipToBottom ? 'top-full mt-2' : 'bottom-full mb-2'}`}>
            {title && <div className="text-center whitespace-normal mb-2">{title}</div>}
            {url && (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-1.5 text-purple-400 hover:text-purple-300 transition-colors"
                onClick={(e) => e.stopPropagation()}
              >
                <span>Open announcement</span>
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            )}
            <div className={`absolute left-1/2 -translate-x-1/2 border-4 border-transparent ${flipToBottom ? 'bottom-full border-b-gray-900' : 'top-full border-t-gray-900'}`}></div>
          </div>
        </>
      )}
    </div>
  );
}

// Game cell with mobile-friendly tooltip
function GameCell({ game }: { game: Game }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [tooltipPos, setTooltipPos] = useState<{ top: number; left: number; placeBelow: boolean } | null>(null);
  const triggerRef = useRef<HTMLDivElement>(null);

  // Get the primary store URL (Steam preferred, then primary_platform, then first available)
  const primaryPlatform = game.steam_id ? 'steam' : game.primary_platform;
  const storeUrl = getStoreUrl(game, primaryPlatform);
  const platformInfo = PLATFORM_INFO[primaryPlatform];

  const updateTooltipPosition = useCallback(() => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    const tooltipHeight = 120; // Approximate tooltip height
    const spaceAbove = rect.top;
    const spaceBelow = window.innerHeight - rect.bottom;
    const placeBelow = spaceAbove < tooltipHeight && spaceBelow > spaceAbove;

    setTooltipPos({
      top: placeBelow ? rect.bottom + 8 : rect.top - 8,
      left: rect.left,
      placeBelow,
    });
  }, []);

  const handleMouseEnter = () => {
    if ('ontouchstart' in window) return; // Skip on touch devices
    setIsHovered(true);
    updateTooltipPosition();
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
  };

  const handleTouch = (e: React.TouchEvent) => {
    e.preventDefault();
    e.stopPropagation();
    updateTooltipPosition();
    setIsOpen(true);
  };

  const handleDesktopClick = (e: React.MouseEvent) => {
    // On desktop, open link directly if we have a store URL
    if (!('ontouchstart' in window)) {
      e.stopPropagation();
      if (storeUrl) {
        window.open(storeUrl, '_blank');
      }
    } else {
      // On touch, show tooltip
      e.preventDefault();
      e.stopPropagation();
      updateTooltipPosition();
      setIsOpen(true);
    }
  };

  const tooltipContent = (showStoreLink: boolean, placeBelow: boolean) => (
    <>
      <div className="font-semibold text-purple-200 mb-1">{game.name}</div>
      {game.developer && <div className="text-gray-400 mb-2">{game.developer}</div>}
      {game.short_description && (
        <div className={`text-gray-400 text-xs line-clamp-3 ${showStoreLink && storeUrl ? 'mb-2' : ''}`}>{game.short_description}</div>
      )}
      {showStoreLink && storeUrl && (
        <a
          href={storeUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-1.5 text-purple-400 hover:text-purple-300 transition-colors mt-2 pt-2 border-t border-purple-700/30"
          onClick={(e) => e.stopPropagation()}
        >
          <span>View on {platformInfo.name}</span>
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      )}
      <div className={`absolute left-4 border-4 border-transparent ${placeBelow ? 'bottom-full border-b-gray-900' : 'top-full border-t-gray-900'}`}></div>
    </>
  );

  return (
    <div ref={triggerRef} className="relative">
      <div
        className="group cursor-pointer hover:text-purple-300 transition-colors"
        onClick={handleDesktopClick}
        onTouchStart={handleTouch}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        <div className="font-semibold text-purple-200 hover:text-purple-300 hover:underline flex items-start gap-1.5">
          <span className="break-words">{game.name}</span>
          <svg className="w-3.5 h-3.5 opacity-0 group-hover:opacity-70 sm:transition-opacity flex-shrink-0 hidden sm:block mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
          {/* Mobile link indicator - always visible */}
          <svg className="w-3.5 h-3.5 opacity-50 flex-shrink-0 sm:hidden mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </div>
        <div className="text-xs text-gray-500">{game.developer || 'Unknown'}</div>
      </div>

      {/* Desktop hover tooltip - rendered via portal */}
      {isHovered && game.short_description && tooltipPos && createPortal(
        <div
          className="hidden sm:block pointer-events-none fixed px-3 py-2 text-xs text-gray-200 bg-gray-900 border border-purple-700/50 rounded-lg z-50 shadow-xl w-64"
          style={{
            top: tooltipPos.placeBelow ? tooltipPos.top : undefined,
            bottom: tooltipPos.placeBelow ? undefined : window.innerHeight - tooltipPos.top,
            left: tooltipPos.left,
          }}
        >
          {tooltipContent(false, tooltipPos.placeBelow)}
        </div>,
        document.body
      )}

      {/* Mobile tap tooltip - rendered via portal */}
      {isOpen && tooltipPos && createPortal(
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
            onTouchStart={() => setIsOpen(false)}
          />
          <div
            className="fixed px-3 py-2 text-xs text-gray-200 bg-gray-900 border border-purple-700/50 rounded-lg z-50 shadow-xl w-64"
            style={{
              top: tooltipPos.placeBelow ? tooltipPos.top : undefined,
              bottom: tooltipPos.placeBelow ? undefined : window.innerHeight - tooltipPos.top,
              left: tooltipPos.left,
            }}
          >
            {tooltipContent(true, tooltipPos.placeBelow)}
          </div>
        </>,
        document.body
      )}
    </div>
  );
}

// Tooltip wrapper component for cell values (only used for Centrality) - desktop only
function CellTooltip({ children, text, flipToBottom = false }: { children: React.ReactNode; text: string; flipToBottom?: boolean }) {
  return (
    <div className="group relative inline-block">
      {children}
      {flipToBottom ? (
        <div className="pointer-events-none absolute top-full left-1/2 -translate-x-1/2 mt-2 px-3 py-2 text-xs text-gray-200 bg-gray-900 border border-purple-700/50 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-normal w-64 text-center z-50 shadow-xl">
          {text}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-gray-900"></div>
        </div>
      ) : (
        <div className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 text-xs text-gray-200 bg-gray-900 border border-purple-700/50 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-normal w-64 text-center z-50 shadow-xl">
          {text}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
        </div>
      )}
    </div>
  );
}

// Tooltip for genres overflow
function GenresTooltip({ children, genres, flipToBottom = false }: { children: React.ReactNode; genres: string[]; flipToBottom?: boolean }) {
  if (genres.length === 0) return <>{children}</>;

  return (
    <div className="group relative inline-block">
      {children}
      {flipToBottom ? (
        <div className="pointer-events-none absolute top-full left-1/2 -translate-x-1/2 mt-2 px-3 py-2 text-xs text-gray-200 bg-gray-900 border border-purple-700/50 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 shadow-xl">
          {genres.join(', ')}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-gray-900"></div>
        </div>
      ) : (
        <div className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 text-xs text-gray-200 bg-gray-900 border border-purple-700/50 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 shadow-xl">
          {genres.join(', ')}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
        </div>
      )}
    </div>
  );
}

// Simple help icon with just a description (no value list)
function SimpleHelpIcon({ title, description }: { title: string; description: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const [popoverPos, setPopoverPos] = useState<{ top: number; left: number } | null>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const updatePosition = useCallback(() => {
    if (!buttonRef.current) return;
    const rect = buttonRef.current.getBoundingClientRect();
    setPopoverPos({
      top: rect.bottom + 8,
      left: rect.left + rect.width / 2,
    });
  }, []);

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (!isOpen) {
      updatePosition();
    }
    setIsOpen(!isOpen);
  };

  return (
    <div className="relative inline-block ml-1">
      <button
        ref={buttonRef}
        onClick={handleClick}
        className="inline-flex items-center justify-center w-4 h-4 text-xs text-purple-400 hover:text-purple-200 border border-purple-500/50 rounded-full hover:border-purple-400 transition-colors"
        aria-label={`Help for ${title}`}
      >
        ?
      </button>
      {isOpen && popoverPos && createPortal(
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={(e) => {
              e.stopPropagation();
              e.preventDefault();
              setIsOpen(false);
            }}
          />
          <div
            className="fixed w-72 bg-gray-900 border border-purple-700/50 rounded-lg shadow-xl z-50 p-3 whitespace-normal -translate-x-1/2"
            style={{
              top: popoverPos.top,
              left: popoverPos.left,
            }}
            onClick={(e) => {
              e.stopPropagation();
              e.preventDefault();
            }}
          >
            <div className="text-sm font-semibold text-purple-300 mb-1">{title}</div>
            <div className="text-xs text-gray-400">{description}</div>
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-gray-900"></div>
          </div>
        </>,
        document.body
      )}
    </div>
  );
}

// Help icon with popover showing all values for a column
function HelpIcon({ info, alignRight = false }: { info: typeof TAXONOMY_INFO.centrality; alignRight?: boolean }) {
  const [isOpen, setIsOpen] = useState(false);
  const [popoverPos, setPopoverPos] = useState<{ top: number; left: number } | null>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const updatePosition = useCallback(() => {
    if (!buttonRef.current) return;
    const rect = buttonRef.current.getBoundingClientRect();
    setPopoverPos({
      top: rect.bottom + 8,
      left: alignRight ? rect.right : rect.left + rect.width / 2,
    });
  }, [alignRight]);

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (!isOpen) {
      updatePosition();
    }
    setIsOpen(!isOpen);
  };

  return (
    <div className="relative inline-block ml-1">
      <button
        ref={buttonRef}
        onClick={handleClick}
        className="inline-flex items-center justify-center w-4 h-4 text-xs text-purple-400 hover:text-purple-200 border border-purple-500/50 rounded-full hover:border-purple-400 transition-colors"
        aria-label={`Help for ${info.title}`}
      >
        ?
      </button>
      {isOpen && popoverPos && createPortal(
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={(e) => {
              e.stopPropagation();
              e.preventDefault();
              setIsOpen(false);
            }}
          />
          <div
            className={`fixed w-72 bg-gray-900 border border-purple-700/50 rounded-lg shadow-xl z-50 p-3 whitespace-normal ${
              alignRight ? '-translate-x-full' : '-translate-x-1/2'
            }`}
            style={{
              top: popoverPos.top,
              left: popoverPos.left,
            }}
            onClick={(e) => {
              e.stopPropagation();
              e.preventDefault();
            }}
          >
            <div className="text-sm font-semibold text-purple-300 mb-1">{info.title}</div>
            <div className="text-xs text-gray-400 mb-3">{info.description}</div>
            <div className="space-y-2">
              {info.values.map((v) => (
                <div key={v.key} className="flex gap-2">
                  <span className={`font-mono ${v.color} w-24 flex-shrink-0`}>{v.label}</span>
                  <span className="text-xs text-gray-400">{v.description}</span>
                </div>
              ))}
            </div>
            {!alignRight && (
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-gray-900"></div>
            )}
          </div>
        </>,
        document.body
      )}
    </div>
  );
}

export default function GamesTable({ games }: GamesTableProps) {
  const [globalFilter, setGlobalFilter] = useState('');
  const [isSubmissionFormOpen, setIsSubmissionFormOpen] = useState(false);
  const [isFilterPanelOpen, setIsFilterPanelOpen] = useState(false);
  const [filters, setFilters] = useState<FilterState>(initialFilterState);
  const filterButtonRef = useRef<HTMLButtonElement>(null);
  const filterPanelRef = useRef<HTMLDivElement>(null);

  // Close filter panel when clicking outside
  useEffect(() => {
    if (!isFilterPanelOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      const clickedButton = filterButtonRef.current?.contains(target);
      const clickedPanel = filterPanelRef.current?.contains(target);

      if (!clickedButton && !clickedPanel) {
        setIsFilterPanelOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isFilterPanelOpen]);

  // Extract unique genres from games data
  const availableGenres = useMemo(() => {
    const genreSet = new Set<string>();
    games.forEach((game) => game.genres.forEach((g) => genreSet.add(g)));
    return Array.from(genreSet).sort();
  }, [games]);

  // Count active filters for badge
  const activeFilterCount = countActiveFilters(filters);

  // Clear all filters
  const clearFilters = () => setFilters(initialFilterState);

  // Combined filter value that triggers re-filtering when either search or filters change
  const combinedFilterValue = useMemo(
    () => ({ search: globalFilter, filters }),
    [globalFilter, filters]
  );

  const columns = useMemo<ColumnDef<Game>[]>(
    () => [
      {
        accessorKey: 'name',
        header: 'Game',
        cell: info => <GameCell game={info.row.original} />,
      },
      {
        id: 'platforms',
        header: 'Platforms',
        cell: info => <PlatformIcons game={info.row.original} flipToBottom={info.row.index === 0} />,
      },
      {
        accessorKey: 'price_usd',
        header: 'Price',
        cell: info => {
          const price = info.getValue() as number | null | undefined;
          if (price === null || price === undefined) {
            return <span className="text-xs text-green-400">Free</span>;
          }
          if (price === 0) {
            return <span className="text-xs text-green-400">Free</span>;
          }
          return <span className="text-xs text-gray-300">${price.toFixed(2)}</span>;
        },
      },
      {
        accessorKey: 'genres',
        header: 'Genres/Tags',
        cell: info => {
          const genres = info.getValue() as string[];
          const hiddenGenres = genres.slice(2);
          const isFirstRow = info.row.index === 0;
          return (
            <div className="flex flex-wrap gap-1">
              {genres.slice(0, 2).map((genre, i) => (
                <span key={i} className="text-xs px-2 py-0.5 bg-gray-800 rounded text-gray-400">
                  {genre}
                </span>
              ))}
              {hiddenGenres.length > 0 && (
                <GenresTooltip genres={hiddenGenres} flipToBottom={isFirstRow}>
                  <span className="text-xs text-gray-500 cursor-help">+{hiddenGenres.length}</span>
                </GenresTooltip>
              )}
            </div>
          );
        },
      },
      {
        accessorKey: 'last_announcement',
        header: 'Latest Announcement',
        cell: info => {
          const date = info.getValue() as string | undefined;
          if (!date) return <span className="text-xs text-gray-600">None</span>;
          return (
            <LinkedCellWithTooltip
              date={date}
              url={info.row.original.last_announcement_url}
              title={info.row.original.last_announcement_title}
              flipToBottom={info.row.index === 0}
            />
          );
        },
      },
      {
        accessorKey: 'last_update',
        header: () => (
          <span className="flex items-center">
            Game Last Updated
            <SimpleHelpIcon
              title="Game Last Updated"
              description="Date of announcement corresponding to a patch, release, hotfix, or other update to the game itself. This is an automatically detected property and may miss updates."
            />
          </span>
        ),
        cell: info => {
          const date = info.getValue() as string | undefined;
          if (!date) return <span className="text-xs text-gray-600">Never</span>;
          return (
            <LinkedCellWithTooltip
              date={date}
              url={info.row.original.last_update_url}
              title={info.row.original.last_update_title}
              flipToBottom={info.row.index === 0}
            />
          );
        },
      },
      // Degree of Necromancy column group - moved to far right
      {
        id: 'degree_of_necromancy',
        header: () => (
          <span className="text-purple-400 font-semibold">Degree of Necromancy</span>
        ),
        columns: [
          {
            accessorKey: 'dimension_1',
            header: () => (
              <span className="flex items-center">
                Centrality
                <HelpIcon info={TAXONOMY_INFO.centrality} />
              </span>
            ),
            sortingFn: centralitySortFn,
            cell: info => {
              const val = info.getValue() as string;
              const valueInfo = TAXONOMY_INFO.centrality.values.find(v => v.key === val);
              if (!valueInfo) return null;
              return (
                <CellTooltip text={valueInfo.description} flipToBottom={info.row.index === 0}>
                  <span className={`font-mono ${valueInfo.color} cursor-help`}>
                    {valueInfo.label}
                  </span>
                </CellTooltip>
              );
            },
          },
          {
            accessorKey: 'dimension_2',
            header: () => (
              <span className="flex items-center">
                POV
                <HelpIcon info={TAXONOMY_INFO.pov} />
              </span>
            ),
            cell: info => {
              const val = info.getValue() as string;
              const valueInfo = TAXONOMY_INFO.pov.values.find(v => v.key === val);
              if (!valueInfo) return null;
              return (
                <span className={`text-sm ${valueInfo.color} capitalize`}>
                  {valueInfo.label}
                </span>
              );
            },
          },
          {
            accessorKey: 'dimension_3',
            header: () => (
              <span className="flex items-center">
                Naming
                <HelpIcon info={TAXONOMY_INFO.naming} alignRight />
              </span>
            ),
            cell: info => {
              const val = info.getValue() as string;
              const valueInfo = TAXONOMY_INFO.naming.values.find(v => v.key === val);
              if (!valueInfo) return null;
              return (
                <span className={`text-sm ${valueInfo.color} capitalize`}>
                  {valueInfo.label}
                </span>
              );
            },
          },
        ],
      },
    ],
    []
  );

  const table = useReactTable({
    data: games,
    columns,
    state: {
      globalFilter: combinedFilterValue,
    },
    globalFilterFn: combinedFilterFn,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: {
        pageSize: 20,
      },
      sorting: [
        {
          id: 'last_announcement',
          desc: true,
        },
      ],
    },
  });

  return (
    <div>
      {/* Search Bar, Filters, and Submission Link */}
      <div className="mb-6">
        <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 sm:items-center">
          {/* Filters Button */}
          <button
            ref={filterButtonRef}
            onClick={() => setIsFilterPanelOpen(!isFilterPanelOpen)}
            className={`flex-shrink-0 px-4 py-3 rounded-lg border transition-colors flex items-center gap-2 text-sm font-medium ${
              isFilterPanelOpen || activeFilterCount > 0
                ? 'bg-purple-900/50 border-purple-500 text-purple-200'
                : 'bg-gray-800 border-purple-700 text-gray-300 hover:border-purple-600 hover:text-purple-200'
            }`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            Filters
            {activeFilterCount > 0 && (
              <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-semibold bg-purple-500 text-white rounded-full">
                {activeFilterCount}
              </span>
            )}
          </button>

          {/* Search Bar */}
          <div className="flex-1">
            <input
              type="text"
              value={globalFilter ?? ''}
              onChange={e => setGlobalFilter(e.target.value)}
              placeholder="Search by game or developer..."
              className="w-full px-4 py-3 bg-gray-800 border border-purple-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20"
            />
          </div>

          {/* Submit Link */}
          <div className="flex-shrink-0 text-center sm:text-left flex flex-col justify-center py-1">
            <span className="text-gray-500 text-sm">Know something we don't?</span>
            <button
              onClick={() => setIsSubmissionFormOpen(true)}
              className="text-purple-400 hover:text-purple-300 text-sm underline underline-offset-2 transition-colors"
            >
              Submit a game
            </button>
          </div>
        </div>

        {/* Filter Panel */}
        {isFilterPanelOpen && (
          <div ref={filterPanelRef}>
            <FilterPanel
              filters={filters}
              onChange={setFilters}
              availableGenres={availableGenres}
              onClear={clearFilters}
              matchingCount={table.getFilteredRowModel().rows.length}
              totalCount={games.length}
            />
          </div>
        )}
      </div>

      {/* Submission Form Modal */}
      <SubmissionForm
        isOpen={isSubmissionFormOpen}
        onClose={() => setIsSubmissionFormOpen(false)}
      />

      {/* Table */}
      <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg border border-purple-700/30 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              {table.getHeaderGroups().map((headerGroup, groupIndex) => (
                <tr key={headerGroup.id} className="border-b border-purple-700/30">
                  {headerGroup.headers.map(header => {
                    // Check if this is the group header row (first row with group headers)
                    const isGroupHeader = groupIndex === 0 && header.colSpan > 1;
                    // Check if this is a sub-column of the taxonomy group
                    const isTaxonomyColumn = header.column.parent?.id === 'degree_of_necromancy';

                    return (
                      <th
                        key={header.id}
                        colSpan={header.colSpan}
                        className={`px-4 py-3 text-left text-sm font-semibold bg-gray-900/50 ${
                          isGroupHeader
                            ? 'text-purple-400 border-b border-purple-600/30 text-center'
                            : 'text-purple-300'
                        } ${
                          isTaxonomyColumn ? 'bg-purple-900/20' : ''
                        } ${
                          header.column.id === 'name' ? 'w-72 min-w-64' : ''
                        } ${
                          header.column.id === 'genres' ? 'w-32 max-w-40' : ''
                        }`}
                      >
                        {header.isPlaceholder ? null : (
                          <div
                            className={`whitespace-nowrap inline-flex items-center gap-1 ${header.column.getCanSort() ? 'cursor-pointer select-none hover:text-purple-200' : ''}`}
                            onClick={header.column.getToggleSortingHandler()}
                          >
                            {flexRender(
                              header.column.columnDef.header,
                              header.getContext()
                            )}
                            {{
                              asc: <span className="flex-shrink-0">↑</span>,
                              desc: <span className="flex-shrink-0">↓</span>,
                            }[header.column.getIsSorted() as string] ?? null}
                          </div>
                        )}
                      </th>
                    );
                  })}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map(row => (
                <tr
                  key={row.id}
                  className="border-b border-gray-700/30 hover:bg-purple-900/20 transition-colors"
                >
                  {row.getVisibleCells().map(cell => {
                    const isTaxonomyColumn = cell.column.parent?.id === 'degree_of_necromancy';
                    return (
                      <td
                        key={cell.id}
                        className={`px-4 py-4 text-sm text-gray-300 ${
                          isTaxonomyColumn ? 'bg-purple-900/10' : ''
                        } ${
                          cell.column.id === 'name' ? 'w-72 min-w-64' : ''
                        } ${
                          cell.column.id === 'genres' ? 'w-32 max-w-40' : ''
                        }`}
                      >
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext()
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-4 py-3 border-t border-purple-700/30 bg-gray-900/50 flex items-center justify-between flex-wrap gap-2">
          <div className="text-sm text-gray-400">
            Showing {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1} to{' '}
            {Math.min(
              (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
              table.getFilteredRowModel().rows.length
            )}{' '}
            of {table.getFilteredRowModel().rows.length} games
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => table.setPageIndex(0)}
              disabled={!table.getCanPreviousPage()}
              className="px-3 py-1 bg-purple-700 text-white rounded disabled:opacity-30 disabled:cursor-not-allowed hover:bg-purple-600 transition-colors text-sm"
            >
              First
            </button>
            <button
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="px-3 py-1 bg-purple-700 text-white rounded disabled:opacity-30 disabled:cursor-not-allowed hover:bg-purple-600 transition-colors text-sm"
            >
              Previous
            </button>
            <button
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="px-3 py-1 bg-purple-700 text-white rounded disabled:opacity-30 disabled:cursor-not-allowed hover:bg-purple-600 transition-colors text-sm"
            >
              Next
            </button>
            <button
              onClick={() => table.setPageIndex(table.getPageCount() - 1)}
              disabled={!table.getCanNextPage()}
              className="px-3 py-1 bg-purple-700 text-white rounded disabled:opacity-30 disabled:cursor-not-allowed hover:bg-purple-600 transition-colors text-sm"
            >
              Last
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
