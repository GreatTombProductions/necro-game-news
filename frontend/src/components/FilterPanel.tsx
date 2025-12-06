import { Fragment, useState } from 'react';

// Types
export interface NecromancyFilter {
  centrality: 'a' | 'b' | 'c' | 'd';
  pov: 'character' | 'unit';
  naming: 'explicit' | 'implied';
}

export interface FilterState {
  genres: string[];
  announcementDateFrom: string;
  announcementDateTo: string;
  lastUpdatedFrom: string;
  lastUpdatedTo: string;
  priceMin: string;
  priceMax: string;
  includeEarlyAccess: boolean;
  necromancyGrid: NecromancyFilter[];
}

// Necromancy dimension keys
const CENTRALITY_KEYS = ['a', 'b', 'c', 'd'] as const;
const POV_KEYS = ['character', 'unit'] as const;
const NAMING_KEYS = ['explicit', 'implied'] as const;

// Generate all 16 necromancy combinations
export function getAllNecromancyCombinations(): NecromancyFilter[] {
  const combinations: NecromancyFilter[] = [];
  for (const centrality of CENTRALITY_KEYS) {
    for (const pov of POV_KEYS) {
      for (const naming of NAMING_KEYS) {
        combinations.push({ centrality, pov, naming });
      }
    }
  }
  return combinations;
}

// Initial state with all necromancy checkboxes checked
export const initialFilterState: FilterState = {
  genres: [],
  announcementDateFrom: '',
  announcementDateTo: '',
  lastUpdatedFrom: '',
  lastUpdatedTo: '',
  priceMin: '',
  priceMax: '',
  includeEarlyAccess: true,
  necromancyGrid: getAllNecromancyCombinations(),
};

interface FilterPanelProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  availableGenres: string[];
  onClear: () => void;
  matchingCount: number;
  totalCount: number;
}

// Necromancy dimension labels
const CENTRALITY_LABELS: Record<string, string> = {
  a: 'Core',
  b: 'Dedicated Spec',
  c: 'Isolated',
  d: 'Minimal',
};

// Helper to check if a combination is selected
function isSelected(
  grid: NecromancyFilter[],
  centrality: string,
  pov: string,
  naming: string
): boolean {
  return grid.some(
    (f) => f.centrality === centrality && f.pov === pov && f.naming === naming
  );
}

// Necromancy Grid Component
function NecromancyGrid({
  value,
  onChange,
}: {
  value: NecromancyFilter[];
  onChange: (grid: NecromancyFilter[]) => void;
}) {
  const toggleCell = (centrality: string, pov: string, naming: string) => {
    const exists = isSelected(value, centrality, pov, naming);
    if (exists) {
      onChange(
        value.filter(
          (f) =>
            !(f.centrality === centrality && f.pov === pov && f.naming === naming)
        )
      );
    } else {
      onChange([
        ...value,
        {
          centrality: centrality as NecromancyFilter['centrality'],
          pov: pov as NecromancyFilter['pov'],
          naming: naming as NecromancyFilter['naming'],
        },
      ]);
    }
  };

  // Helper to get all combinations for a row (centrality level)
  const getRowCombinations = (centrality: string): NecromancyFilter[] => {
    const combinations: NecromancyFilter[] = [];
    for (const pov of POV_KEYS) {
      for (const naming of NAMING_KEYS) {
        combinations.push({
          centrality: centrality as NecromancyFilter['centrality'],
          pov,
          naming,
        });
      }
    }
    return combinations;
  };

  // Helper to get all combinations for a column (naming type across all)
  const getColumnCombinations = (pov: typeof POV_KEYS[number], naming: typeof NAMING_KEYS[number]): NecromancyFilter[] => {
    return CENTRALITY_KEYS.map((centrality) => ({
      centrality,
      pov,
      naming,
    }));
  };

  // Helper to get all combinations for a POV group (character or unit)
  const getPovCombinations = (pov: typeof POV_KEYS[number]): NecromancyFilter[] => {
    const combinations: NecromancyFilter[] = [];
    for (const centrality of CENTRALITY_KEYS) {
      for (const naming of NAMING_KEYS) {
        combinations.push({
          centrality,
          pov,
          naming,
        });
      }
    }
    return combinations;
  };

  // Check if all combinations in a group are selected
  const areAllSelected = (combinations: NecromancyFilter[]): boolean => {
    return combinations.every((c) =>
      value.some(
        (v) => v.centrality === c.centrality && v.pov === c.pov && v.naming === c.naming
      )
    );
  };

  // Toggle all combinations in a group (select all if any unselected, deselect all if all selected)
  const toggleGroup = (combinations: NecromancyFilter[]) => {
    const allSelected = areAllSelected(combinations);
    if (allSelected) {
      // Deselect all in group
      onChange(
        value.filter(
          (v) =>
            !combinations.some(
              (c) => c.centrality === v.centrality && c.pov === v.pov && c.naming === v.naming
            )
        )
      );
    } else {
      // Select all in group (add missing ones)
      const missing = combinations.filter(
        (c) =>
          !value.some(
            (v) => v.centrality === c.centrality && v.pov === c.pov && v.naming === c.naming
          )
      );
      onChange([...value, ...missing]);
    }
  };

  const selectAllCheckboxClass = "w-4 h-4 rounded border-purple-500 bg-gray-600 text-purple-400 focus:ring-purple-500 focus:ring-offset-gray-800 cursor-pointer";

  return (
    <div className="overflow-x-auto">
      <table className="text-xs">
        <thead>
          <tr>
            <th className="px-2 py-1"></th>
            <th className="px-2 py-1"></th>
            <th colSpan={2} className="px-2 py-1 text-center border-b border-purple-700/30">
              <label className="flex items-center justify-center gap-1.5 cursor-pointer text-purple-300">
                <input
                  type="checkbox"
                  checked={areAllSelected(getPovCombinations('character'))}
                  onChange={() => toggleGroup(getPovCombinations('character'))}
                  className={selectAllCheckboxClass}
                />
                Character
              </label>
            </th>
            <th className="px-1 text-gray-600">|</th>
            <th colSpan={2} className="px-2 py-1 text-center border-b border-purple-700/30">
              <label className="flex items-center justify-center gap-1.5 cursor-pointer text-purple-300">
                <input
                  type="checkbox"
                  checked={areAllSelected(getPovCombinations('unit'))}
                  onChange={() => toggleGroup(getPovCombinations('unit'))}
                  className={selectAllCheckboxClass}
                />
                Unit
              </label>
            </th>
          </tr>
          <tr>
            <th className="px-2 py-1"></th>
            <th className="px-2 py-1"></th>
            <th className="px-2 py-1 text-center text-gray-400 font-normal">Explicit</th>
            <th className="px-2 py-1 text-center text-gray-400 font-normal">Implied</th>
            <th className="px-1 text-gray-600">|</th>
            <th className="px-2 py-1 text-center text-gray-400 font-normal">Explicit</th>
            <th className="px-2 py-1 text-center text-gray-400 font-normal">Implied</th>
          </tr>
        </thead>
        <tbody>
          {CENTRALITY_KEYS.map((centrality) => (
            <tr key={centrality}>
              <td className="px-2 py-1 text-gray-300 font-medium whitespace-nowrap">
                {CENTRALITY_LABELS[centrality]}
              </td>
              {/* Row select-all checkbox */}
              <td className="px-2 py-1 text-center">
                <input
                  type="checkbox"
                  checked={areAllSelected(getRowCombinations(centrality))}
                  onChange={() => toggleGroup(getRowCombinations(centrality))}
                  className={selectAllCheckboxClass}
                  title={`Select all ${CENTRALITY_LABELS[centrality]}`}
                />
              </td>
              {POV_KEYS.map((pov, povIndex) => (
                <Fragment key={pov}>
                  {povIndex === 1 && (
                    <td className="px-1 text-gray-600">|</td>
                  )}
                  {NAMING_KEYS.map((naming) => (
                    <td key={`${centrality}-${pov}-${naming}`} className="px-2 py-1 text-center">
                      <input
                        type="checkbox"
                        checked={isSelected(value, centrality, pov, naming)}
                        onChange={() => toggleCell(centrality, pov, naming)}
                        className="w-4 h-4 rounded border-purple-600 bg-gray-700 text-purple-500 focus:ring-purple-500 focus:ring-offset-gray-800 cursor-pointer"
                      />
                    </td>
                  ))}
                </Fragment>
              ))}
            </tr>
          ))}
          {/* Column select-all row */}
          <tr className="border-t border-purple-700/30">
            <td className="px-2 py-1"></td>
            <td className="px-2 py-1"></td>
            {POV_KEYS.map((pov, povIndex) => (
              <Fragment key={pov}>
                {povIndex === 1 && (
                  <td className="px-1 text-gray-600">|</td>
                )}
                {NAMING_KEYS.map((naming) => (
                  <td key={`col-${pov}-${naming}`} className="px-2 py-1 text-center">
                    <input
                      type="checkbox"
                      checked={areAllSelected(getColumnCombinations(pov, naming))}
                      onChange={() => toggleGroup(getColumnCombinations(pov, naming))}
                      className={selectAllCheckboxClass}
                      title={`Select all ${pov} ${naming}`}
                    />
                  </td>
                ))}
              </Fragment>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  );
}

// Multi-select Genres Component
function GenreSelect({
  value,
  onChange,
  availableGenres,
}: {
  value: string[];
  onChange: (genres: string[]) => void;
  availableGenres: string[];
}) {
  const [isOpen, setIsOpen] = useState(false);

  const toggleGenre = (genre: string) => {
    if (value.includes(genre)) {
      onChange(value.filter((g) => g !== genre));
    } else {
      onChange([...value, genre]);
    }
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-2 bg-gray-700 border border-purple-700/50 rounded-lg text-left text-sm text-gray-300 hover:border-purple-600 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 flex items-center justify-between"
      >
        <span className={value.length === 0 ? 'text-gray-500' : ''}>
          {value.length === 0 ? 'Select genres...' : `${value.length} selected`}
        </span>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute top-full left-0 right-0 mt-1 bg-gray-800 border border-purple-700/50 rounded-lg shadow-xl z-50 max-h-48 overflow-y-auto">
            {availableGenres.map((genre) => (
              <label
                key={genre}
                className="flex items-center px-3 py-2 hover:bg-purple-900/30 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={value.includes(genre)}
                  onChange={() => toggleGenre(genre)}
                  className="w-4 h-4 rounded border-purple-600 bg-gray-700 text-purple-500 focus:ring-purple-500 focus:ring-offset-gray-800 mr-2"
                />
                <span className="text-sm text-gray-300">{genre}</span>
              </label>
            ))}
          </div>
        </>
      )}

      {value.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {value.map((genre) => (
            <span
              key={genre}
              className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-900/50 border border-purple-700/50 rounded text-xs text-purple-300"
            >
              {genre}
              <button
                type="button"
                onClick={() => toggleGenre(genre)}
                className="hover:text-purple-100"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// Date Range Input Component
function DateRangeInput({
  label,
  fromValue,
  toValue,
  onFromChange,
  onToChange,
}: {
  label: string;
  fromValue: string;
  toValue: string;
  onFromChange: (value: string) => void;
  onToChange: (value: string) => void;
}) {
  return (
    <div>
      <label className="block text-sm text-gray-400 mb-1">{label}</label>
      <div className="flex gap-2 items-center">
        <input
          type="date"
          value={fromValue}
          onChange={(e) => onFromChange(e.target.value)}
          className="flex-1 px-2 py-1.5 bg-gray-700 border border-purple-700/50 rounded text-sm text-gray-300 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20"
        />
        <span className="text-gray-500 text-sm">to</span>
        <input
          type="date"
          value={toValue}
          onChange={(e) => onToChange(e.target.value)}
          className="flex-1 px-2 py-1.5 bg-gray-700 border border-purple-700/50 rounded text-sm text-gray-300 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20"
        />
      </div>
    </div>
  );
}

// Price Range Input Component
function PriceRangeInput({
  minValue,
  maxValue,
  onMinChange,
  onMaxChange,
}: {
  minValue: string;
  maxValue: string;
  onMinChange: (value: string) => void;
  onMaxChange: (value: string) => void;
}) {
  return (
    <div>
      <label className="block text-sm text-gray-400 mb-1">Price (USD)</label>
      <div className="flex gap-2 items-center">
        <div className="flex-1 relative">
          <span className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-500 text-sm">$</span>
          <input
            type="number"
            min="0"
            step="0.01"
            placeholder="Min"
            value={minValue}
            onChange={(e) => onMinChange(e.target.value)}
            className="w-full pl-5 pr-2 py-1.5 bg-gray-700 border border-purple-700/50 rounded text-sm text-gray-300 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20"
          />
        </div>
        <span className="text-gray-500 text-sm">to</span>
        <div className="flex-1 relative">
          <span className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-500 text-sm">$</span>
          <input
            type="number"
            min="0"
            step="0.01"
            placeholder="Max"
            value={maxValue}
            onChange={(e) => onMaxChange(e.target.value)}
            className="w-full pl-5 pr-2 py-1.5 bg-gray-700 border border-purple-700/50 rounded text-sm text-gray-300 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20"
          />
        </div>
      </div>
    </div>
  );
}

// Main FilterPanel Component
export default function FilterPanel({
  filters,
  onChange,
  availableGenres,
  onClear,
  matchingCount,
  totalCount,
}: FilterPanelProps) {
  const updateFilter = <K extends keyof FilterState>(key: K, value: FilterState[K]) => {
    onChange({ ...filters, [key]: value });
  };

  const hasActiveFilters =
    filters.genres.length > 0 ||
    filters.announcementDateFrom ||
    filters.announcementDateTo ||
    filters.lastUpdatedFrom ||
    filters.lastUpdatedTo ||
    filters.priceMin ||
    filters.priceMax ||
    !filters.includeEarlyAccess ||
    filters.necromancyGrid.length < 16; // Less than all = filter active

  return (
    <div className="mt-4 p-4 bg-gray-800/70 border border-purple-700/30 rounded-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-purple-300">Advanced Filters</h3>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-400">
            {matchingCount} of {totalCount} games
          </span>
          {hasActiveFilters && (
            <button
              type="button"
              onClick={onClear}
              className="text-xs text-gray-400 hover:text-purple-300 transition-colors"
            >
              Clear all
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Genres/Tags */}
        <div>
          <label className="block text-sm text-gray-400 mb-1">Genres/Tags</label>
          <GenreSelect
            value={filters.genres}
            onChange={(genres) => updateFilter('genres', genres)}
            availableGenres={availableGenres}
          />
        </div>

        {/* Date Ranges */}
        <DateRangeInput
          label="Latest News"
          fromValue={filters.announcementDateFrom}
          toValue={filters.announcementDateTo}
          onFromChange={(v) => updateFilter('announcementDateFrom', v)}
          onToChange={(v) => updateFilter('announcementDateTo', v)}
        />

        <DateRangeInput
          label="Last Updated"
          fromValue={filters.lastUpdatedFrom}
          toValue={filters.lastUpdatedTo}
          onFromChange={(v) => updateFilter('lastUpdatedFrom', v)}
          onToChange={(v) => updateFilter('lastUpdatedTo', v)}
        />

        {/* Price Range */}
        <PriceRangeInput
          minValue={filters.priceMin}
          maxValue={filters.priceMax}
          onMinChange={(v) => updateFilter('priceMin', v)}
          onMaxChange={(v) => updateFilter('priceMax', v)}
        />

        {/* Early Access Toggle */}
        <div>
          <label className="block text-sm text-gray-400 mb-1">Early Access</label>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => updateFilter('includeEarlyAccess', !filters.includeEarlyAccess)}
              className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500/20 ${
                filters.includeEarlyAccess ? 'bg-purple-600' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-6 w-6 transform rounded-full bg-white shadow-md transition-transform ${
                  filters.includeEarlyAccess ? 'translate-x-7' : 'translate-x-1'
                }`}
              />
            </button>
            <span className="text-sm text-gray-400">
              {filters.includeEarlyAccess ? 'Included' : 'Excluded'}
            </span>
          </div>
        </div>
      </div>

      {/* Necromancy Grid */}
      <div className="mt-4 pt-4 border-t border-purple-700/30">
        <label className="block text-sm text-gray-400 mb-2">Degree of Necromancy</label>
        <NecromancyGrid
          value={filters.necromancyGrid}
          onChange={(grid) => updateFilter('necromancyGrid', grid)}
        />
        {filters.necromancyGrid.length < 16 && (
          <p className="text-xs text-gray-500 mt-2">
            {filters.necromancyGrid.length} of 16 combinations selected
          </p>
        )}
      </div>
    </div>
  );
}

// Helper function to count active filters (for badge)
export function countActiveFilters(filters: FilterState): number {
  let count = 0;
  if (filters.genres.length > 0) count++;
  if (filters.announcementDateFrom || filters.announcementDateTo) count++;
  if (filters.lastUpdatedFrom || filters.lastUpdatedTo) count++;
  if (filters.priceMin || filters.priceMax) count++;
  if (!filters.includeEarlyAccess) count++;
  if (filters.necromancyGrid.length < 16) count++; // Only count if some are deselected
  return count;
}
