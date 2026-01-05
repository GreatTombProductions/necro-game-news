import { useMemo, useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import type { Game, Platform } from '../types';
import { PLATFORM_INFO, getStoreUrl } from '../types';

interface NewsItem {
  game: Game;
  date: Date;
  title: string;
  url?: string;
  content?: string;
}

// Truncate text to a max length, adding ellipsis if needed
function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  // Try to break at a word boundary
  const truncated = text.slice(0, maxLength);
  const lastSpace = truncated.lastIndexOf(' ');
  if (lastSpace > maxLength * 0.7) {
    return truncated.slice(0, lastSpace) + '...';
  }
  return truncated + '...';
}

interface NewsFeedProps {
  games: Game[];  // Already filtered by search/filters
}

// Format relative time (e.g., "2 days ago", "3 weeks ago")
function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays <= 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 14) return '1 week ago';
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  return `${Math.floor(diffDays / 30)} month${Math.floor(diffDays / 30) > 1 ? 's' : ''} ago`;
}

// Platform icon components
function SteamIcon({ className }: { className?: string }) {
  return <img src="/icons/steam.svg" alt="Steam" className={className} />;
}

function BattlenetIcon({ className }: { className?: string }) {
  return <img src="/icons/battlenet.svg" alt="Battle.net" className={`${className} invert`} />;
}

function PlatformIcon({ platform }: { platform: Platform }) {
  const iconClass = "w-4 h-4";
  const info = PLATFORM_INFO[platform];

  switch (platform) {
    case 'steam':
      return <SteamIcon className={iconClass} />;
    case 'battlenet':
      return <BattlenetIcon className={iconClass} />;
    default:
      return <span className="text-sm">{info?.icon || '🎮'}</span>;
  }
}

// Calculate tooltip position with viewport awareness
function calculateTooltipPosition(
  rect: DOMRect,
  tooltipWidth: number,
  tooltipHeight: number
): { top: number; left: number; placeBelow: boolean } {
  const padding = 8;

  // Vertical positioning
  const spaceAbove = rect.top;
  const spaceBelow = window.innerHeight - rect.bottom;
  const placeBelow = spaceAbove < tooltipHeight && spaceBelow > spaceAbove;
  const top = placeBelow ? rect.bottom + 8 : rect.top - 8;

  // Horizontal positioning - center on element
  let left = rect.left + rect.width / 2 - tooltipWidth / 2;

  // Constrain to viewport
  const maxLeft = window.innerWidth - tooltipWidth - padding;
  const minLeft = padding;
  left = Math.max(minLeft, Math.min(maxLeft, left));

  return { top, left, placeBelow };
}

// Individual news item with tooltip
function NewsItemRow({ item }: { item: NewsItem }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [tooltipPos, setTooltipPos] = useState<{ top: number; left: number; placeBelow: boolean } | null>(null);
  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const primaryPlatform = item.game.steam_id ? 'steam' : item.game.primary_platform;
  const storeUrl = getStoreUrl(item.game, primaryPlatform);

  // Close tooltip on scroll or click outside
  useEffect(() => {
    if (!isOpen && !isHovered) return;

    const handleScroll = () => {
      setIsOpen(false);
      setIsHovered(false);
    };

    const handleClickOutside = (e: MouseEvent | TouchEvent) => {
      const target = e.target as Node;
      const clickedTrigger = triggerRef.current?.contains(target);
      const clickedTooltip = tooltipRef.current?.contains(target);
      if (!clickedTrigger && !clickedTooltip) {
        setIsOpen(false);
      }
    };

    window.addEventListener('scroll', handleScroll, true);
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('touchstart', handleClickOutside);
    }

    return () => {
      window.removeEventListener('scroll', handleScroll, true);
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [isOpen, isHovered]);

  const updateTooltipPosition = useCallback(() => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    const tooltipWidth = 320; // w-80
    const tooltipHeight = 100;
    setTooltipPos(calculateTooltipPosition(rect, tooltipWidth, tooltipHeight));
  }, []);

  const handleMouseEnter = () => {
    if ('ontouchstart' in window) return;
    updateTooltipPosition();
    setIsHovered(true);
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

  const handleClick = (e: React.MouseEvent) => {
    // On touch devices, show tooltip first
    if ('ontouchstart' in window) {
      e.preventDefault();
      e.stopPropagation();
      updateTooltipPosition();
      setIsOpen(true);
    }
    // On desktop, let the link work normally (handled by the anchor elements)
  };

  const tooltipContent = (showLinks: boolean) => (
    <>
      {/* Full title */}
      <div className="text-sm font-medium text-gray-200 mb-1 break-words">{item.title}</div>

      {/* Game info */}
      <div className="text-xs text-gray-500 mb-2">
        {item.game.name} • {formatRelativeTime(item.date)}
      </div>

      {/* Content preview */}
      {item.content && (
        <div className="text-xs text-gray-400 mb-2 leading-relaxed break-words">
          {truncateText(item.content, 200)}
        </div>
      )}

      {/* Link for mobile */}
      {showLinks && item.url && (
        <div className="pt-2 border-t border-purple-700/30">
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-1.5 text-purple-400 hover:text-purple-300 transition-colors text-xs"
            onClick={(e) => e.stopPropagation()}
          >
            <span>Read announcement</span>
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        </div>
      )}
    </>
  );

  return (
    <div
      ref={triggerRef}
      className="px-4 py-3 hover:bg-purple-900/10 transition-colors cursor-pointer"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onTouchStart={handleTouch}
      onClick={handleClick}
    >
      <div className="flex items-start gap-3">
        {/* Platform icon */}
        <div className="flex-shrink-0 mt-0.5 opacity-70">
          <PlatformIcon platform={primaryPlatform} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2 flex-wrap">
            {/* Game name - desktop link, mobile shows in tooltip */}
            {storeUrl ? (
              <a
                href={storeUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="hidden sm:inline text-sm font-medium text-purple-200 hover:text-purple-100 hover:underline"
                onClick={(e) => e.stopPropagation()}
              >
                {item.game.name}
              </a>
            ) : null}
            <span className="sm:hidden text-sm font-medium text-purple-200">
              {item.game.name}
            </span>
            {!storeUrl && (
              <span className="hidden sm:inline text-sm font-medium text-purple-200">
                {item.game.name}
              </span>
            )}

            {/* Time ago */}
            <span className="text-xs text-gray-500 flex-shrink-0">
              {formatRelativeTime(item.date)}
            </span>
          </div>

          {/* News title - desktop link, mobile shows in tooltip */}
          {item.url ? (
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:block text-xs text-gray-400 hover:text-purple-300 line-clamp-1 mt-0.5"
              onClick={(e) => e.stopPropagation()}
            >
              {item.title}
            </a>
          ) : (
            <p className="hidden sm:block text-xs text-gray-500 line-clamp-1 mt-0.5">
              {item.title}
            </p>
          )}
          {/* Mobile: truncated title without link */}
          <p className="sm:hidden text-xs text-gray-400 line-clamp-1 mt-0.5">
            {item.title}
          </p>
        </div>
      </div>

      {/* Desktop hover tooltip - rendered via portal */}
      {isHovered && tooltipPos && createPortal(
        <div
          className="hidden sm:block pointer-events-none fixed px-3 py-2 text-gray-200 bg-gray-900 border border-purple-700/50 rounded-lg z-50 shadow-xl w-80 overflow-hidden"
          style={{
            top: tooltipPos.placeBelow ? tooltipPos.top : undefined,
            bottom: tooltipPos.placeBelow ? undefined : window.innerHeight - tooltipPos.top,
            left: tooltipPos.left,
          }}
        >
          {tooltipContent(false)}
        </div>,
        document.body
      )}

      {/* Mobile tap tooltip - rendered via portal */}
      {isOpen && tooltipPos && createPortal(
        <div
          ref={tooltipRef}
          className="fixed px-3 py-2 text-gray-200 bg-gray-900 border border-purple-700/50 rounded-lg z-50 shadow-xl w-80 overflow-hidden"
          style={{
            top: tooltipPos.placeBelow ? tooltipPos.top : undefined,
            bottom: tooltipPos.placeBelow ? undefined : window.innerHeight - tooltipPos.top,
            left: tooltipPos.left,
          }}
        >
          {tooltipContent(true)}
        </div>,
        document.body
      )}
    </div>
  );
}

export default function NewsFeed({ games }: NewsFeedProps) {
  // Start collapsed on mobile (< 640px, Tailwind's sm breakpoint)
  const [isCollapsed, setIsCollapsed] = useState(() =>
    typeof window !== 'undefined' && window.innerWidth < 640
  );

  // Get news items from filtered games, limited to last 30 days
  const newsItems = useMemo(() => {
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

    const items: NewsItem[] = [];

    for (const game of games) {
      if (game.last_announcement) {
        const date = new Date(game.last_announcement);
        if (date >= thirtyDaysAgo) {
          items.push({
            game,
            date,
            title: game.last_announcement_title || 'New announcement',
            url: game.last_announcement_url,
            content: game.last_announcement_content,
          });
        }
      }
    }

    // Sort by date, newest first
    items.sort((a, b) => b.date.getTime() - a.date.getTime());

    return items;
  }, [games]);

  // Don't render if no news items
  if (newsItems.length === 0) {
    return null;
  }

  return (
    <div className="mb-6">
      {/* Header with collapse toggle */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="w-full flex items-center justify-between px-4 py-2 bg-gray-800/50 border border-purple-700/30 rounded-t-lg hover:bg-gray-800/70 transition-colors"
      >
        <div className="flex items-center gap-2">
          <svg
            className={`w-4 h-4 text-purple-400 transition-transform ${isCollapsed ? '-rotate-90' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
          <span className="text-sm font-medium text-purple-300">
            Recent News
          </span>
          <span className="text-xs text-gray-500">
            ({newsItems.length} {newsItems.length === 1 ? 'update' : 'updates'} in last 30 days)
          </span>
        </div>
        <span className="text-xs text-gray-500">
          {isCollapsed ? 'Show' : 'Hide'}
        </span>
      </button>

      {/* News items container */}
      {!isCollapsed && (
        <div className="bg-gray-800/30 border border-t-0 border-purple-700/30 rounded-b-lg overflow-hidden">
          {/* Scrollable news list - max height shows ~4 items */}
          <div className="max-h-64 overflow-y-auto divide-y divide-purple-700/20">
            {newsItems.map((item, index) => (
              <NewsItemRow key={`${item.game.id}-${index}`} item={item} />
            ))}
          </div>

          {/* Footer with helper text */}
          <div className="px-4 py-2 text-xs text-gray-500 text-center border-t border-purple-700/20">
            {newsItems.length > 4 ? 'Scroll for more • ' : ''}Use filters to narrow results
          </div>
        </div>
      )}
    </div>
  );
}
