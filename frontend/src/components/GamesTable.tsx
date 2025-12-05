import { useMemo, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  flexRender,
} from '@tanstack/react-table';
import type { ColumnDef, FilterFn } from '@tanstack/react-table';
import type { Game } from '../types';

interface GamesTableProps {
  games: Game[];
}

// Tooltip descriptions for taxonomy columns
const TAXONOMY_TOOLTIPS = {
  dimension_1: {
    a: 'Necromancy is central to the character or unit\'s identity and gameplay',
    b: 'Cohesive set of necromantic skills or equipment available to specialize into',
    c: 'One or more necromantic skills or equipment exist, but are not grouped into a cohesive category',
    d: 'Necromancy is technically available to the character or unit, but with minimal impact to their identity and gameplay',
  },
  dimension_2: {
    character: 'Play AS the necromancer (who may control other necromancers)',
    unit: 'Play as some entity controlling one or more necromancers, but not as any of them',
  },
  dimension_3: {
    explicit: 'An exact or minor variant of "necromancer" or "necromancy" used in game',
    implied: 'Necromancy not mentioned by name in game',
  },
};

// Custom filter function that searches name, developer, and genres
const gameFilterFn: FilterFn<Game> = (row, _columnId, filterValue) => {
  const search = filterValue.toLowerCase();
  const game = row.original;

  // Strip special characters for matching
  const normalize = (str: string) => str.toLowerCase().replace(/[®©™]/g, '');

  // Search in name
  if (normalize(game.name).includes(search)) return true;

  // Search in developer
  if (game.developer && normalize(game.developer).includes(search)) return true;

  // Search in genres
  if (game.genres?.some(genre => normalize(genre).includes(search))) return true;

  // Search in steam tags
  if (game.steam_tags?.some(tag => normalize(tag).includes(search))) return true;

  return false;
};

// Tooltip wrapper component
function Tooltip({ children, text }: { children: React.ReactNode; text: string }) {
  return (
    <div className="group relative inline-block">
      {children}
      <div className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 text-xs text-gray-200 bg-gray-900 border border-purple-700/50 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-normal w-64 text-center z-50 shadow-xl">
        {text}
        <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
      </div>
    </div>
  );
}

export default function GamesTable({ games }: GamesTableProps) {
  const [globalFilter, setGlobalFilter] = useState('');

  const columns = useMemo<ColumnDef<Game>[]>(
    () => [
      {
        accessorKey: 'name',
        header: 'Game',
        cell: info => (
          <div
            className="cursor-pointer hover:text-purple-300 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              window.open(`https://store.steampowered.com/app/${info.row.original.steam_id}`, '_blank');
            }}
          >
            <div className="font-semibold text-purple-200">{info.getValue() as string}</div>
            <div className="text-xs text-gray-500">{info.row.original.developer || 'Unknown'}</div>
          </div>
        ),
      },
      // Taxonomy column group
      {
        id: 'taxonomy',
        header: () => (
          <span className="text-purple-400 font-semibold">Necromancy Taxonomy</span>
        ),
        columns: [
          {
            accessorKey: 'dimension_1',
            header: 'Centrality',
            cell: info => {
              const val = info.getValue() as string;
              const labels: Record<string, string> = { a: 'Core', b: 'Dedicated Spec', c: 'Isolated', d: 'Minimal' };
              const colors: Record<string, string> = {
                a: 'text-green-400',
                b: 'text-blue-400',
                c: 'text-yellow-400',
                d: 'text-gray-400'
              };
              return (
                <Tooltip text={TAXONOMY_TOOLTIPS.dimension_1[val as keyof typeof TAXONOMY_TOOLTIPS.dimension_1]}>
                  <span className={`font-mono ${colors[val]} cursor-help`}>
                    {labels[val]}
                  </span>
                </Tooltip>
              );
            },
          },
          {
            accessorKey: 'dimension_2',
            header: 'POV',
            cell: info => {
              const val = info.getValue() as string;
              return (
                <Tooltip text={TAXONOMY_TOOLTIPS.dimension_2[val as keyof typeof TAXONOMY_TOOLTIPS.dimension_2]}>
                  <span className="text-sm text-purple-300 capitalize cursor-help">{val}</span>
                </Tooltip>
              );
            },
          },
          {
            accessorKey: 'dimension_3',
            header: 'Naming',
            cell: info => {
              const val = info.getValue() as string;
              return (
                <Tooltip text={TAXONOMY_TOOLTIPS.dimension_3[val as keyof typeof TAXONOMY_TOOLTIPS.dimension_3]}>
                  <span className={`text-sm ${val === 'explicit' ? 'text-green-300' : 'text-blue-300'} capitalize cursor-help`}>
                    {val}
                  </span>
                </Tooltip>
              );
            },
          },
        ],
      },
      {
        accessorKey: 'genres',
        header: 'Genres',
        cell: info => {
          const genres = info.getValue() as string[];
          return (
            <div className="flex flex-wrap gap-1">
              {genres.slice(0, 2).map((genre, i) => (
                <span key={i} className="text-xs px-2 py-0.5 bg-gray-800 rounded text-gray-400">
                  {genre}
                </span>
              ))}
              {genres.length > 2 && (
                <span className="text-xs text-gray-500">+{genres.length - 2}</span>
              )}
            </div>
          );
        },
      },
      {
        accessorKey: 'last_update',
        header: 'Last Update',
        cell: info => {
          const date = info.getValue() as string | undefined;
          const url = info.row.original.last_update_url;

          if (!date) return <span className="text-xs text-gray-600">Never</span>;

          let formatted: string;
          try {
            formatted = new Date(date).toLocaleDateString();
          } catch {
            formatted = date;
          }

          if (url) {
            return (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-gray-400 hover:text-purple-300 hover:underline transition-colors"
                onClick={(e) => e.stopPropagation()}
              >
                {formatted}
              </a>
            );
          }

          return <span className="text-xs text-gray-500">{formatted}</span>;
        },
      },
      {
        accessorKey: 'last_announcement',
        header: 'Last Announcement',
        cell: info => {
          const date = info.getValue() as string | undefined;
          const url = info.row.original.last_announcement_url;

          if (!date) return <span className="text-xs text-gray-600">None</span>;

          let formatted: string;
          try {
            formatted = new Date(date).toLocaleDateString();
          } catch {
            formatted = date;
          }

          if (url) {
            return (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-gray-400 hover:text-purple-300 hover:underline transition-colors"
                onClick={(e) => e.stopPropagation()}
              >
                {formatted}
              </a>
            );
          }

          return <span className="text-xs text-gray-500">{formatted}</span>;
        },
      },
    ],
    []
  );

  const table = useReactTable({
    data: games,
    columns,
    state: {
      globalFilter,
    },
    onGlobalFilterChange: setGlobalFilter,
    globalFilterFn: gameFilterFn,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: {
        pageSize: 20,
      },
    },
  });

  return (
    <div>
      {/* Search Bar */}
      <div className="mb-6">
        <input
          type="text"
          value={globalFilter ?? ''}
          onChange={e => setGlobalFilter(e.target.value)}
          placeholder="Search games, developers, genres..."
          className="w-full px-4 py-3 bg-gray-800 border border-purple-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20"
        />
      </div>

      {/* Table */}
      <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg border border-purple-700/30 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              {table.getHeaderGroups().map(headerGroup => (
                <tr key={headerGroup.id} className="border-b border-purple-700/30">
                  {headerGroup.headers.map(header => (
                    <th
                      key={header.id}
                      colSpan={header.colSpan}
                      className="px-4 py-4 text-left text-sm font-semibold text-purple-300 bg-gray-900/50"
                    >
                      {header.isPlaceholder ? null : (
                        <div
                          className={header.column.getCanSort() ? 'cursor-pointer select-none hover:text-purple-200' : ''}
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          {flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                          {{
                            asc: ' ↑',
                            desc: ' ↓',
                          }[header.column.getIsSorted() as string] ?? null}
                        </div>
                      )}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map(row => (
                <tr
                  key={row.id}
                  className="border-b border-gray-700/30 hover:bg-purple-900/20 transition-colors"
                >
                  {row.getVisibleCells().map(cell => (
                    <td key={cell.id} className="px-4 py-4 text-sm text-gray-300">
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </td>
                  ))}
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
