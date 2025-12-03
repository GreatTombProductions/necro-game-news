import { useMemo, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  flexRender,
} from '@tanstack/react-table';
import type { ColumnDef } from '@tanstack/react-table';
import type { Game } from '../types';

interface GamesTableProps {
  games: Game[];
}

export default function GamesTable({ games }: GamesTableProps) {
  const [globalFilter, setGlobalFilter] = useState('');

  const columns = useMemo<ColumnDef<Game>[]>(
    () => [
      {
        accessorKey: 'name',
        header: 'Game',
        cell: info => (
          <div>
            <div className="font-semibold text-purple-200">{info.getValue() as string}</div>
            <div className="text-xs text-gray-500">{info.row.original.developer || 'Unknown'}</div>
          </div>
        ),
      },
      {
        accessorKey: 'dimension_1',
        header: 'Centrality',
        cell: info => {
          const val = info.getValue() as string;
          const labels: Record<string, string> = { a: 'Core', b: 'Spec', c: 'Isolated', d: 'Flavor' };
          const colors: Record<string, string> = { 
            a: 'text-green-400', 
            b: 'text-blue-400', 
            c: 'text-yellow-400', 
            d: 'text-gray-400' 
          };
          return (
            <span className={`font-mono ${colors[val]}`}>
              {labels[val]}
            </span>
          );
        },
      },
      {
        accessorKey: 'dimension_2',
        header: 'POV',
        cell: info => (
          <span className="text-sm text-purple-300 capitalize">{info.getValue() as string}</span>
        ),
      },
      {
        accessorKey: 'dimension_3',
        header: 'Naming',
        cell: info => {
          const val = info.getValue() as string;
          return (
            <span className={`text-sm ${val === 'explicit' ? 'text-green-300' : 'text-blue-300'} capitalize`}>
              {val}
            </span>
          );
        },
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
        accessorKey: 'update_count',
        header: 'Updates',
        cell: info => (
          <span className="text-gray-400">{info.getValue() as number}</span>
        ),
      },
      {
        accessorKey: 'last_update',
        header: 'Last Update',
        cell: info => {
          const date = info.getValue() as string | undefined;
          if (!date) return <span className="text-xs text-gray-600">Never</span>;
          try {
            const formatted = new Date(date).toLocaleDateString();
            return <span className="text-xs text-gray-500">{formatted}</span>;
          } catch {
            return <span className="text-xs text-gray-500">{date}</span>;
          }
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
                  className="border-b border-gray-700/30 hover:bg-purple-900/20 transition-colors cursor-pointer"
                  onClick={() => window.open(`https://store.steampowered.com/app/${row.original.steam_id}`, '_blank')}
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